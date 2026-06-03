import { PresetSchema } from "./types";

export const PRESETS: PresetSchema[] = [
  {
    id: "pharmaceutical",
    name: "Фармацевтика (Pharmacy)",
    description: "Разбор аптечных прайс-листов: бренды, формы выпуска, дозировки лекарственных препаратов и упаковка.",
    labels: [
      { key: "brand", label: "BRAND", color: "from-amber-500/10 to-amber-500/20 text-amber-500 border-amber-500/30", title: "Бренд" },
      { key: "form", label: "FORM", color: "from-blue-500/10 to-blue-500/20 text-blue-400 border-blue-500/30", title: "Форма" },
      { key: "dose", label: "DOSE", color: "from-emerald-500/10 to-emerald-500/20 text-emerald-400 border-emerald-500/30", title: "Дозировка" },
      { key: "pack", label: "PACK", color: "from-indigo-500/10 to-indigo-500/20 text-indigo-400 border-indigo-500/30", title: "Упаковка" }
    ],
    defaultRecords: [
      { brand: "Супрастин", form: "таблетки", dose: "25мг", pack: "№20" },
      { brand: "Вольтарен Экспресс", form: "капсулы", dose: "12.5мг", pack: "10 шт" },
      { brand: "Нурофен Экспресс Леди", form: "капсулы", dose: "400мг", pack: "№12" },
      { brand: "Аспирин Кардио", form: "таблетки п/о", dose: "100мг", pack: "28 шт" },
      { brand: "Терафлю", form: "порошок для сусп.", dose: "325мг/20мг/10мг", pack: "10 пакетиков" },
      { brand: "Но-Шпа Forte", form: "таблетки", dose: "80мг", pack: "№24" },
      { brand: "Линекс Форте", form: "капсулы", dose: "60мг/12мг", pack: "№14" },
      { brand: "Пенталгин", form: "таблетки п/о", dose: "325мг+50мг+10мг", pack: "24 шт" },
      { brand: "Канефрон Н", form: "драже", dose: "18мг", pack: "№60" },
      { brand: "Дюфалак", form: "сироп", dose: "66.7г/100мл", pack: "500мл" }
    ]
  },
  {
    id: "addresses",
    name: "Адреса и Локации (Addresses)",
    description: "Парсинг почтовых адресов и географических локаций в отдельные структурированные компоненты.",
    labels: [
      { key: "city", label: "CITY", color: "from-sky-500/10 to-sky-500/20 text-sky-400 border-sky-500/30", title: "Город" },
      { key: "street", label: "STREET", color: "from-rose-500/10 to-rose-500/20 text-rose-400 border-rose-500/30", title: "Улица" },
      { key: "building", label: "BUILDING", color: "from-orange-500/10 to-orange-500/20 text-orange-400 border-orange-500/30", title: "Дом / Корпус" },
      { key: "zip", label: "ZIP", color: "from-teal-500/10 to-teal-500/20 text-teal-400 border-teal-500/30", title: "Индекс" }
    ],
    defaultRecords: [
      { city: "Москва", street: "Тверская", building: "д. 7 ст. 1", zip: "125009" },
      { city: "Санкт-Петербург", street: "Невский проспект", building: "дом 12, кв 4", zip: "191186" },
      { city: "Новосибирск", street: "Красный проспект", building: "35а", zip: "630099" },
      { city: "Екатеринбург", street: "8 Марта", building: "строение 8Б", zip: "620014" },
      { city: "Казань", street: "Баумана", building: "21", zip: "420111" },
      { city: "Владивосток", street: "Светланская", building: "д 44 оф 3", zip: "690091" },
      { city: "Сочи", street: "Курортный проспект", building: "дом 83", zip: "354002" }
    ]
  },
  {
    id: "financial",
    name: "Финансовые документы (Invoices)",
    description: "Извлечение метаданных из первичных финансовых документов, счетов-фактур и платежей.",
    labels: [
      { key: "vendor", label: "VENDOR", color: "from-fuchsia-500/10 to-fuchsia-500/20 text-fuchsia-400 border-fuchsia-500/30", title: "Поставщик" },
      { key: "invoice_no", label: "INVOICE", color: "from-cyan-500/10 to-cyan-500/20 text-cyan-400 border-cyan-500/30", title: "Номер счета" },
      { key: "amount", label: "AMOUNT", color: "from-lime-500/10 to-lime-500/20 text-lime-400 border-lime-500/30", title: "Сумма" },
      { key: "currency", label: "CURR", color: "from-purple-500/10 to-purple-500/20 text-purple-400 border-purple-500/30", title: "Валюта" }
    ],
    defaultRecords: [
      { vendor: "ООО Ромашка Трейд", invoice_no: "№152-A-2026", amount: "45200.50", currency: "RUB" },
      { vendor: "АО Яндекс Облачные Сервисы", invoice_no: "INV-77491-05", amount: "125000.00", currency: "RUB" },
      { vendor: "Google Ireland Ltd PLC", invoice_no: "G-55122-EU", amount: "99.99", currency: "USD" },
      { vendor: "ИП Петров Консалтинг", invoice_no: "СЧ-4993-24", amount: "5400.00", currency: "EUR" },
      { vendor: "ПАО Мегафон Корп", invoice_no: "ТЛФ-48821", amount: "1290.00", currency: "RUB" }
    ]
  }
];
