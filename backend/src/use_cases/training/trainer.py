"""Обучение spaCy NER-модели: подготовка .spacy, конфиг, обучение и упаковка в zip."""

import asyncio
import json
import random
import shutil
from pathlib import Path

import spacy
from spacy.tokens import DocBin

from src.use_cases.training.augmentation import Sample

# Базовые модели spaCy в порядке отображения. Реально скачанные определяются на лету.
BASE_MODEL_ORDER = ('ru_core_news_sm', 'ru_core_news_md', 'ru_core_news_lg')
SUPPORTED_BASE_MODELS = set(BASE_MODEL_ORDER)
# Модели без статических векторов (для них не задаём initialize.vectors).
_MODELS_WITHOUT_VECTORS = {'ru_core_news_sm'}


def installed_base_models() -> set[str]:
    """Возвращает множество базовых моделей, реально установленных в окружении."""
    return {model for model in BASE_MODEL_ORDER if spacy.util.is_package(model)}


class SpacyTrainingError(RuntimeError):
    """Ошибка процесса обучения spaCy."""


class SpacyTrainer:
    """Готовит данные и обучает spaCy NER-модель в рабочей папке задачи."""

    def __init__(self, workdir: Path, base_model: str, epochs: int, dropout: float) -> None:
        self.workdir = workdir
        self.base_model = base_model
        self.epochs = epochs
        self.dropout = dropout
        self.train_path = workdir / 'train.spacy'
        self.dev_path = workdir / 'dev.spacy'
        self.config_path = workdir / 'config.cfg'
        self.output_path = workdir / 'output'

    async def prepare(self, samples: list[Sample]) -> None:
        """Разбивает выборку на train/dev, пишет .spacy и генерирует config.cfg."""
        await asyncio.to_thread(self._write_docbins, samples)
        await self._init_config()

    def _write_docbins(self, samples: list[Sample]) -> None:
        """Конвертирует примеры в бинарный формат spaCy с train/dev сплитом ~85/15."""
        shuffled = list(samples)
        random.Random(0).shuffle(shuffled)
        split = max(1, int(len(shuffled) * 0.85))
        train_samples = shuffled[:split]
        dev_samples = shuffled[split:] or shuffled[:1]

        nlp = spacy.blank('ru')
        self._build_docbin(nlp, train_samples).to_disk(self.train_path)
        self._build_docbin(nlp, dev_samples).to_disk(self.dev_path)

    @staticmethod
    def _build_docbin(nlp: spacy.Language, samples: list[Sample]) -> DocBin:
        """Собирает DocBin из примеров, отбрасывая спаны, не легшие на границы токенов."""
        doc_bin = DocBin()
        for text, entities in samples:
            doc = nlp.make_doc(text)
            spans = []
            for start, end, label in entities:
                span = doc.char_span(start, end, label=label, alignment_mode='contract')
                if span is not None:
                    spans.append(span)
            doc.ents = spans
            doc_bin.add(doc)
        return doc_bin

    async def _init_config(self) -> None:
        """Генерирует базовый конфиг spaCy для NER.

        Модели со статическими векторами (md/lg) обучаем в режиме accuracy и
        подключаем их векторы. Для sm (векторов нет) используем efficiency —
        иначе слой статических векторов падает на пустой таблице векторов.
        """
        optimize = 'efficiency' if self.base_model in _MODELS_WITHOUT_VECTORS else 'accuracy'
        await self._run(
            'init',
            'config',
            str(self.config_path),
            '--lang',
            'ru',
            '--pipeline',
            'ner',
            '--optimize',
            optimize,
            '--force',
        )

    async def train(self) -> tuple[Path, dict]:
        """Запускает обучение, упаковывает model-best в zip и возвращает (zip, метрики)."""
        overrides = [
            '--paths.train',
            str(self.train_path),
            '--paths.dev',
            str(self.dev_path),
            '--training.max_epochs',
            str(self.epochs),
            '--training.max_steps',
            '0',  # ограничиваем обучение эпохами, а не шагами
            '--training.dropout',
            str(self.dropout),
        ]
        # Для моделей со статическими векторами подключаем их как базовые.
        if self.base_model not in _MODELS_WITHOUT_VECTORS:
            overrides += ['--initialize.vectors', self.base_model]

        await self._run(
            'train', str(self.config_path), '--output', str(self.output_path), *overrides
        )

        model_best = self.output_path / 'model-best'
        meta_path = model_best / 'meta.json'
        if not meta_path.exists():
            raise SpacyTrainingError('Обучение завершилось без артефакта model-best.')

        performance = json.loads(meta_path.read_text(encoding='utf-8')).get('performance', {})
        metrics = {
            'ents_f': performance.get('ents_f'),
            'ents_p': performance.get('ents_p'),
            'ents_r': performance.get('ents_r'),
        }

        # Упаковываем готовую модель в zip для скачивания.
        archive_base = str(self.workdir / 'model')
        zip_path = await asyncio.to_thread(
            shutil.make_archive, archive_base, 'zip', str(model_best)
        )
        return Path(zip_path), metrics

    @staticmethod
    async def _run(*args: str) -> None:
        """Запускает `python -m spacy <args>` дочерним процессом и проверяет код возврата."""
        process = await asyncio.create_subprocess_exec(
            'python',
            '-m',
            'spacy',
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await process.communicate()
        if process.returncode != 0:
            output = stdout.decode('utf-8', errors='replace') if stdout else ''
            raise SpacyTrainingError(f'spaCy завершился с кодом {process.returncode}: {output}')
