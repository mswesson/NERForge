"""Обучение spaCy NER-модели: подготовка .spacy, конфиг и запуск spacy train."""

import asyncio
import json
import random
from pathlib import Path

import spacy
from spacy.tokens import DocBin

from src.use_cases.training.augmentation import Sample


class SpacyTrainingError(RuntimeError):
    """Ошибка процесса обучения spaCy."""


class SpacyTrainer:
    """Готовит данные и обучает spaCy NER-модель в рабочей папке задачи."""

    def __init__(self, workdir: Path) -> None:
        self.workdir = workdir
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
        """Генерирует базовый конфиг spaCy для NER, оптимизированный на точность."""
        await self._run(
            'init',
            'config',
            str(self.config_path),
            '--lang',
            'ru',
            '--pipeline',
            'ner',
            '--optimize',
            'accuracy',
            '--force',
        )

    async def train(self) -> tuple[Path, dict]:
        """Запускает обучение и возвращает путь к model-best и метрики качества."""
        await self._run(
            'train',
            str(self.config_path),
            '--output',
            str(self.output_path),
            '--paths.train',
            str(self.train_path),
            '--paths.dev',
            str(self.dev_path),
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
        return model_best, metrics

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
