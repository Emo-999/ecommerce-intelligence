# Дизайн система CloudCart Admin: задължителни указания

Прочетете това докрай, преди да напишете първия ред код. Документът е обвързващ. 
Той описва рамката, в която работим, и има предимство пред Вашите подразбирания и 
пред подразбиранията на която и да е библиотека. Ако заданието противоречи на този 
документ, кажете за противоречието вместо да го решавате сами.

Настройката е генерирана от playground-а на дизайн системата за конкретен клиент. 
Между продуктите се менят марковият цвят и логото. Шрифтът НЕ е параметър: 
Montserrat е шрифтът на къщата и не се избира. 
Всичко останало (разстояния, радиуси, сенки, семантични роли, компоненти, светла и 
тъмна тема) е еднакво по замисъл и не се пренастройва.

| Параметър | Стойност |
|---|---|
| Проект | Демо Магазин |
| Марков цвят (семе) | `#8D58E0` |
| Шрифтова система | Montserrat — текст, заглавия и кодове, едно семейство за всичко |
| Регистър | админ, плътен: основен текст 13/20 px |
| Лого | няма подадено |
| Случай | съществуващ проект, привеждане към системата |
| Генерирано | 08.08.2026 · дизайн система CloudCart Admin Design System 1.0 |

Придружаващи файлове от същата настройка: `design.json` (машинно четимата версия, 
която проверката преди пускане търси в корена на проекта) и `theme.css` (същият 
стилов файл, който е вграден по-долу в §3).

---

## 1. Правилата, които не се нарушават

### 1.1 Марковият цвят се появява на шест места и никъде другаде

1. запълване на основния бутон (`--general-primary`),
2. връзки и текстови бутони (`--general-primary`),
3. фокус пръстен (`--focus-ring`),
4. избран ред и активен елемент в навигацията, като тон от 5 до 8 % 
   (`--sidebar-sidebar-accent`), никога плътно,
5. подчертаване на активния таб,
6. включени контроли: чекбокс, радио, ключ.

Всичко структурно е неутрално: странична лента, горна лента, фон на страницата, 
карти, таблици, заглавия. Около 1 до 3 % от пикселите носят нюанс. Оцветена в 
марката странична лента е първият признак за остаряла администрация. Логото носи 
своите цветове и не се пребоядисва, но то е изображение, не интерфейсен елемент.

### 1.2 Рамки, не сенки

Разделянето става с рамка от 1 px и със стъпка в светлотата на равнината. Три 
равнини, най-тъмната е хромът: странична лента и горна лента < фон на страницата < 
карта и таблица. Данните са най-светлото нещо на екрана. В тъмна тема принципът е 
същият, но равнините изсветляват, докато се издигат.

Сянка има само това, което наистина плава и се затваря с клик встрани: меню, 
изскачащ слой, модален прозорец, влачен елемент. Карта, плочка, таблица, KPI блок, 
залепена лента и закотвена колона нямат сянка: страничната или горната „drop shadow“ 
върху кутия или лента е най-сигурният белег за генериран дизайн (решение от 
07.08.2026). Лентите и закотвените колони се отделят с рамка от 1 px. Никога няма 
преливки, матово стъкло или размиване на фона.

### 1.3 Разстояния, радиуси и типография само от токените

Всяка стойност идва от променлива от §3. Сурово число в стил се пише само там, 
където токен няма, и до него стои коментар защо. Мрежата е 4 px. Композицията диша, 
данните са плътни: вътрешно поле на карта 20 px, разстояние между карти 20 до 24 px, 
между секции 32 до 40 px, поле на страницата 32 px, въздух под заглавието на 
страницата поне 24 px. Редовете на таблицата са с под 44 px и 6 px вертикално поле 
в клетката: ред с повече съдържание расте, никога не се притиска. Лента с търсене, 
филтри или инструменти никога не лепне за рамка: поне 16 px до ръба на картата или 
до съседния блок, включително отгоре. Когато екранът се усеща натъпкан, махнете 
елемент или добавете въздух, никога не смалявайте шрифта.

### 1.4 Правилата срещу вида „писано от изкуствен интелект“

1. Никакво дълго тире в интерфейсни низове, етикети, имена на продукти и съобщения. 
   Ползвайте запетая, двоеточие или пренапишете изречението. Празна клетка в таблица 
   е кратко тире „–“.
2. Никакви емоджи. Иконите са вграден SVG (Lucide), включително превключвателят на 
   темата: слънце и луна като SVG, не като знаци. Правилото важи и за разметката, 
   родена от JavaScript: празни състояния, известия и грешки, изписани от скрипт, 
   се проверяват отделно — там емоджи оцелява месеци, защото никой не претърсва `.js`.
3. Никакво движение при посочване. Без `translateY`, без `scale`, без повдигане. 
   Посочването сменя фон, рамка или цвят за 100 ms и нищо друго.
4. Никакви декоративни сенки (вж. 1.2).
5. Никакви преливки, матово стъкло, лилаво-сини акценти по подразбиране, центрирано 
   всичко и номерирана украса (01/02/03), освен ако наистина е поредица.
6. Йерархията се носи от размер, тегло и цвят, не от кутии. Проверка: екранът остава 
   четим и с изключени рамки.
7. Никакви цветни акцентни ленти по ръба на карта, плочка или ред (горе или 
   отстрани). Акцентът живее в съдържанието: точка, значка, оцветен текст.

### 1.5 Български конвенции

- `<html lang="bg">` винаги. Интерфейсът е на български, на Вие, с изречен регистър 
  на главните букви (не Заглавен Регистър, това е английска привичка).
- Бутоните са глаголи: „Запази“, „Отказ“, „Импортирай“, „Добави продукт“, „Изтрий“. 
  Никога „Запазване на промените“ върху бутон.
- Речник: Табло · Продукти · Категории · Поръчки · Клиенти · Импорт · Задачи · 
  Настройки · Екип · Роли · Търсене · Филтри · Изчисти всички · Записани изгледи · 
  Незапазени промени · Завършеност · Наличност · Още.
- Дати `24.07.2026` с точки, часовете в 24 часов формат. До 7 дни може относително 
  („преди 2 ч.“), след това абсолютно.
- Числа с интервал за хилядите и запетая за десетичните: `1 240,50`. Валутата е след 
  числото: `1 240,50 лв.`, `634,26 €`.
- Празните състояния цитират филтъра обратно: „Няма продукти за „тениска бяла“. 
  Изчистете филтрите.“

### 1.6 Респонсив регистър

Плътно на десктоп, удобно на телефон. Плътността е решение само за десктопа.

- **1280 и нагоре**: страничната лента е 240 px разгъната.
- **1024 до 1279**: лентата се свива до 64 px релса с икони.
- **768 до 1023**: релса с икони, поле на страницата 24, KPI плочки 2 по 2, дясната 
  колона на детайлната страница слиза под основната, таблиците пускат колоните с 
  нисък приоритет (остават снимка, име, цена, статус).
- **под 768**: основният текст става 15 px, всички полета 16 px (иначе iOS увеличава 
  при фокус), контролите стават 40 px, целите за докосване поне 44 px. Навигацията 
  влиза в чекмедже отляво плюс долна лента с четири таба (Табло · Продукти · Задачи · 
  Още). Редовете на таблиците стават карти. Лентата за запазване става долна лента 
  на цялата ширина и замества таба, докато има промени.

**Инверсията на типа се прави в КОРЕНА, не по компоненти.** Предефинирайте 
`--fs-body`, `--fs-body-sm`, `--fs-caption` и водачите им вътре в телефонната 
заявка: така всичко, което чете токените, расте наведнъж. Правено компонент по 
компонент, все нещо остава на 12 px. Водачът пътува с кегела — 15 px текст на 
водач от 20 px диша по-малко от 13-те, които замества. 16-те пиксела на полетата 
са константа на платформата (прагът, под който iOS увеличава при фокус), а не 
стъпка от типовата скала — не ги „закръгляйте“ към нея.

**Чекмеджето дължи пет неща**, не едно: затваряне при клик върху затъмнението, 
при `Escape`, при плъзгане наляво, връщане на фокуса там, откъдето е дошъл, и 
пазач при преоразмеряване — завъртането на телефона настрани минава границата и 
трябва да пусне заключения скрол, иначе страницата остава замразена без чекмедже. 
Страничната лента и долната лента се раждат от ЕДИН списък: това е една и съща 
навигация, написана два пъти, и се разминава при първия нов раздел. Инструментите 
от горната лента, които не се побират до заглавието (тема, изход, преглед като 
роля), слизат в чекмеджето — не се смаляват и не изчезват.

**Не всяка таблица става карти.** Списъчните таблици — да; композицията зависи от 
това какво Е заглавието: късо име дели първия ред със стойността (име отляво, цена 
отдясно), а заглавие-изречение (задача, тикет, заявка) взема първия ред само за 
себе си и лентата с признаци (номер, статус, стойност) отива на втория. Числовите 
решетки (бонуси, матрици с KPI, матрицата с правата) НЕ стават карти — четенето 
напряко през реда им е целият им смисъл; те скролват настрани със закотвена първа 
колона, на която се слага максимална ширина, за да остане място за числата. 
Механиката: ролята се обявява на `<th>` (`title` / `trail` / `sub` / `drop` / 
`actions`), няколко реда скрипт свалят заглавието на колоната върху клетките като 
`data-label`, а CSS прави оформлението. Без JavaScript таблицата си остава таблица 
със страничен скрол. ⚠️ Скриването на колони на таблета виси на този скрипт: скрито 
`<th>` с видими `<td>`-та разминава всеки ред.

**Хоризонталното преливане на телефон е ФУНКЦИОНАЛЕН дефект.** Когато страницата е 
по-широка от изгледа, мобилният Chrome смалява целия документ, за да го побере: 
`innerWidth` се връща ПО-ГОЛЯМ от устройството (390 → 421) и всичко с 
`position: fixed` излиза ПОД видимото поле. Така долната лента изчезва от един 
екран, докато на всички останали изглежда наред. Проверявайте го машинно, не с 
очи: заредете всеки екран на 320 / 390 / 430 и сравнете `innerWidth` и 
`documentElement.scrollWidth` с ширината на устройството — смалената страница 
изглежда ПРАВИЛНА, просто малко дребна, затова прегледът по снимки я пропуска. 
Четирите причини, които се повтарят: (1) `grid-column: span 2` в решетка, която 
току-що сте свели до една колона — Grid отваря НЕЯВНА втора колона и формата тихо 
остава на две; (2) коловоз `1fr` не пада под min-content на съдържанието си — 
пишете `minmax(0, 1fr)` навсякъде, където има платно на графика, таблица или 
свободен текст; (3) дълги непрекъсваеми низове (адреси, е-поща, идентификатори — 
при нас заглавието на запис често Е адрес): `overflow-wrap: anywhere`, НЕ 
`break-word` — само `anywhere` сваля min-content ширината, а точно тя спира 
свиването на флекс и решетъчните деца; (4) колони с фиксирана ширина за етикет 
в флекс ред — редът трябва да се пренася, а етикетът да мине на `width: auto`; 
(5) под на коловоз `minmax(340px, 1fr)` не се свива — пишете 
`minmax(min(340px, 100%), 1fr)`.

**`100vh` е грешната единица на телефон.** `vh` е ГОЛЯМАТА рамка: височината 
при ПРИБРАНА адресна лента, тоест по-висока от това, което човекът вижда. 
Като долен праг (`min-height: 100vh` върху обвивката на приложението, върху 
екрана за вход, върху каквото и да е на цяла височина) тя прави документа 
по-висок от екрана на ВСЯКА страница — дори на страница почти без съдържание 
— и излишъкът се скролва в празен фон, което е особено видимо под фиксирана 
долна лента. Праговете вървят на `100svh` (малката рамка, с показана адресна 
лента, тоест най-малкото видимо поле — праг от нея не може да роди скрол), с 
`100vh` обявено ПРЕДИ него като резерв: `min-height: 100vh; min-height: 
100svh`. Каквото трябва да следи видимата височина, докато лентата се скрива 
и връща, върви на `100dvh` — подлепена странична лента на `100vh` увисва с 
долния си блок под ръба на екрана. ⛔ **Симулаторът на устройства НЕ показва 
този дефект**: в емулиран браузър няма прибираща се лента и `100vh`, `100svh`, 
`100dvh` и `innerHeight` дават едно и също число. Проверявайте с твърдение, че 
изчисленият праг е равен на `innerHeight`, а механизма — като нарочно вдигнете 
прага и видите как се появява мъртвият скрол. Височината на долната лента е 
ЕДИН токен, четен на едно място (лентата и просветът под съдържанието), а 
горната лента има свой токен дори когато днес и двете са 56 px — иначе едно 
изместване чете чуждата мярка и се чупи тихо в деня, в който някоя се смени.

**Извън екрана НЕ значи нерисуван.** Чекмедже или панел, паркиран с 
`transform: translateX(100%)`, е изместен от погледа, но остава НАПЪЛНО 
оформен. За един-два слоя това е безплатно; за екран, който ражда по един 
панел на ред (на месец, на запис), е фатално: 26 панела по ~25 контроли и 
343 `<select>` в един документ са 8 392 layout обекта и 16 ms преизчисляване 
на стила — мобилният рендер свършва паметта и разделът умира, докато 
десктопът го е поглъщал незабелязано. **Затвореният слой излиза от потока** 
(`display: none`), а плъзгането се пази на две стъпки: слагате клас за 
анимация, принуждавате един reflow, чак тогава `.open`; при затваряне 
махате `.open` и сваляте класа на `transitionend` — ЗАДЪЛЖИТЕЛНО с резервен 
таймер, защото при `prefers-reduced-motion` преход няма и събитието не идва. 
Същата страница после: 1 637 layout обекта и 2 ms. Предпочитайте `display: 
none` пред пренасяне в `<template>`: DOM-ът остава цял и панелите, които се 
попълват ПРЕДИ да се отворят, продължават да работят без промяна. 
(`content-visibility: hidden` беше измерено и НЕ помага — то не изважда 
фиксирано и трансформирано поддърво от оформлението.)

**Закотвената клетка се рисува ВЪРХУ съседните**, затова първа колона, която 
прелива, ляга върху числата. Иска три неща, не едно: `overflow: hidden` 
(клипът е структурен, не козметичен), ПОД освен таван (`min-width` + `width` 
+ `max-width` — само с таван флексът свива колоната до min-content) и пренос 
по ДУМИ, а не `overflow-wrap: anywhere`, което чупи имена на хора по средата. 
На телефон аватарът и второстепенният етикет за роля излизат от тази колона: 
аватарът само повтаря името с инициали, а всеки от двата струва ред на запис.

**`@container` или `@media`?** Питайте на какво отговаря правилото. Хромът на 
приложението отговаря на УСТРОЙСТВОТО — чекмеджето, долната лента, полето на 
страницата, инверсията на типа: това е `@media`, защото продуктът се отваря в 
истински прозорец, а контейнерна заявка би вързала долната лента за ширината на 
случайна кутия. Компонентът отговаря на СЛОТА си — карта, плочка, таблица, която 
може да влезе в тясна колона: това е `@container` (`container-type: inline-size`), 
и то е същото, което държи симулатора на устройства в макета честен. Макет: 
предимно `@container`. Продукт: `@media` за хрома, `@container` за компонентите.

### 1.7 Фокусът не подлежи на договаряне

Една идиома, навсякъде: `outline: 2px solid var(--focus-ring); outline-offset: 2px`. 
Никакво `outline: none` без незабавна замяна. Всяка контрола има състояния за 
посочване, натискане, фокус и забрана; липсата им се чете като счупено.

---

## 2. Вашият избор, разгърнат

### 2.1 Семейството от семето `#8D58E0`

Семейството е генерирано в OKLCH по кривата на светлотата на Tailwind, после всяка 
роля е решена срещу договора за контраст (WCAG 2.2). Стъпката котва е тази, която е 
най-близо до подадения цвят: 600.

| Стъпка | Hex | Променлива | Ползва се за |
|---|---|---|---|
| 50 | `#F6F3FF` | `--brand-50` | най-светъл фон, рядко |
| 100 | `#ECE5FF` | `--brand-100` | тон на избран ред и на активна навигация |
| 200 | `#DED1FF` | `--brand-200` | тон при посочване |
| 300 | `#C9B1FF` | `--brand-300` | рамка на тонирани блокове |
| 400 | `#AE82FF` | `--brand-400` | светъл вариант |
| 500 | `#9D67F4` | `--brand-500` | плътно запълване, светла тема |
| 600 (котва) | `#8D58E0` | `--brand-600` | плътно запълване и връзки |
| 700 | `#7344BB` | `--brand-700` | посочен основен бутон |
| 800 | `#603A9A` | `--brand-800` | натиснат |
| 900 | `#503380` | `--brand-900` | текст върху тон |
| 950 | `#2A1648` | `--brand-950` | най-тъмен текст |

**Предупреждения на генератора за това семе** (негови думи, на английски). 
Не ги гасете, те са част от решението:

- brand/50: chroma reduced 0.020 -> 0.016 to fit sRGB (constant L and H)
- brand/100: chroma reduced 0.048 -> 0.035 to fit sRGB (constant L and H)
- brand/200: chroma reduced 0.091 -> 0.064 to fit sRGB (constant L and H)
- brand/300: chroma reduced 0.142 -> 0.111 to fit sRGB (constant L and H)
- brand/400: chroma reduced 0.182 -> 0.179 to fit sRGB (constant L and H)
- seed hue 297.9deg is in the blue/violet band, LCH-family hue shift is largest here; worth a manual QA pass

**Корекции на решателя за контраст** (също негови думи). Ролята е преместена на 
друга стъпка от същата стълба, за да мине договорът. Не ги връщайте назад:

- `general/primary`: brand/600 към brand/700 (brand/600 failed solid.primary/text.primary.background/text.primary.card; walked 1 step(s))
- `general/destructive`: red/500 към red/600 (red/500 failed solid.destructive; walked 1 step(s))
- `unofficial/destructive foreground`: red/500 към red/700 (red/500 failed text.destructive.background; walked 2 step(s))
- `focus/ring`: brand/300 към brand/500 (brand/300 failed ui.ring.background; walked 2 step(s))
- `focus/ring error`: red/300 към red/500 (red/300 failed ui.ring-error.background; walked 2 step(s))
- `general/muted foreground`: gray/500 към gray/600 (gray/500 failed text.muted-foreground.muted/text.muted-foreground.background; walked 1 step(s))
- `unofficial/border primary`: brand/600 към brand/700 (same alias and same role noun as an adjusted role; kept in step with it)
- `sidebar/sidebar primary`: brand/600 към brand/700 (same alias and same role noun as an adjusted role; kept in step with it)
- `sidebar/sidebar ring`: brand/300 към brand/500 (same alias and same role noun as an adjusted role; kept in step with it)

### 2.2 Семантичните роли

Компонентите ползват само тези променливи, никога сурово шестнадесетично число и 
никога `--brand-*` направо. Пълните 133 роли са в `theme.css`; ето тези, които се ползват всеки ден:

| Роля | Променлива | Светла | Тъмна | За какво |
|---|---|---|---|---|
| general/background | `--general-background` | `#F4F5F9` | `#0A0A14` | фон на страницата |
| general/foreground | `--general-foreground` | `#24252D` | `#F7F8F8` | основен текст |
| card/card | `--card-card` | `#FFFFFF` | `#1A1A2B` | повърхност на карта и таблица, най-светлата равнина |
| card/card foreground | `--card-card-foreground` | `#24252D` | `#F7F8F8` | текст върху карта |
| general/muted | `--general-muted` | `#EBEDF4` | `#1A1A2B` | приглушена повърхност (заглавен ред на таблица, кротки блокове) |
| general/muted foreground | `--general-muted-foreground` | `#585F71` | `#8C93A4` | второстепенен текст, надписи, мерни единици |
| general/border | `--general-border` | `#DBDEEA` | `#34314E` | рамка, хоризонтална линия |
| general/input | `--general-input` | `#FFFFFF` | `#FFFFFF0D` | фон на поле за въвеждане |
| general/primary | `--general-primary` | `#7344BB` | `#AE82FF` | марковото запълване: основен бутон |
| general/primary foreground | `--general-primary-foreground` | `#FFFFFF` | `#1A1A2B` | надпис върху марково запълване |
| unofficial/primary hover | `--unofficial-primary-hover` | `#9D67F4` | `#C9B1FF` | основен бутон при посочване |
| focus/ring | `--focus-ring` | `#9D67F4` | `#C9B1FF` | фокус пръстен |
| focus/ring error | `--focus-ring-error` | `#FC4F4E` | `#FF6867` | фокус пръстен на поле с грешка |
| general/destructive | `--general-destructive` | `#E91A19` | `#FF6867` | опасно действие, изтриване |
| unofficial/destructive foreground | `--unofficial-destructive-foreground` | `#C51110` | `#FF6867` | текст на грешка под поле |
| sidebar/sidebar | `--sidebar-sidebar` | `#EBEDF4` | `#1A1A2B` | фон на страничната лента |
| sidebar/sidebar foreground | `--sidebar-sidebar-foreground` | `#716E94` | `#C5C9DC` | текст в страничната лента |
| sidebar/sidebar accent | `--sidebar-sidebar-accent` | `#DBDEEA` | `#34314E` | тон на активния елемент в навигацията |
| sidebar/sidebar accent foreground | `--sidebar-sidebar-accent-foreground` | `#1A1A2B` | `#EBEDF4` | текст на активния елемент |
| sidebar/sidebar border | `--sidebar-sidebar-border` | `#C5C9DC` | `#34314E` | рамка на страничната лента |

Ролите за грешка, успех и предупреждение стоят на своя нюанс и не се пребоядисват 
от марката: клиент с магента марка няма магента „успешно“.

### 2.3 Шрифтовата система: Montserrat

1 семейства, 95 KB подрязани. Familiar and warm, the high-usage option, chosen knowingly.

Файловете за сваляне и подрязване (никакъв CDN на Google: подрязвачът им маха 
стилистичните набори и `tnum`, а и е външен произход, което за клиенти в ЕС е тема):

| Фамилия | Роля | Свалете | Запишете като | Лиценз |
|---|---|---|---|---|
| Montserrat | sans, headings, mono | [Montserrat[wght].ttf](https://fonts.google.com/specimen/Montserrat) | `/fonts/montserrat-var.woff2` | OFL-1.1 |

Командата за подрязване е в `docs/FONT-SYSTEMS.md` §3.4; тя пази изрично `locl` и 
`ssNN`, които подразбиращият се списък на `pyftsubset` изхвърля.

```css
@font-face {
  font-family: "Montserrat";
  src: url("/fonts/montserrat-var.woff2") format("woff2-variations");
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
```

**Особености на тези шрифтове.** Всяко от твърденията по-долу е проверено срещу 
двоичния файл, не срещу страница с образци:

- Montserrat: цифрите са пропорционални по подразбиране. Без `font-variant-numeric: tabular-nums lining-nums` на :root колоната с цени подскача.
- Montserrat: носи liga, dlig. В клетки на таблици, SKU и полета лигатурите се гасят изрично, иначе съчетания вътре в кодовете се пренаписват.
- Montserrat: българските форми идват през `locl` и се включват само от `<html lang="bg">` (22 замествания). В Safari `locl` през `lang` исторически е ненадежден, проверете на iOS преди пускане.
- Montserrat: гръцко покритие 8/69. Ако продуктът ще пуска гръцки, сменете тази роля с шрифт с пълен гръцки.

Предпочитайте `font-variant-numeric` пред `font-feature-settings`. Второто заменя, 
а не слива: един компонент, който си сложи свое `font-feature-settings`, мълчаливо 
изтрива всичко наследено. Затова гасенето на лигатурите в клетки е изрично и на 
едно място, както е в `theme.css`.

### 2.4 Типографската стълба, регистър админ

| Роля | Размер / водещо | Тегло | Проследяване | Семейство |
|---|---|---|---|---|
| `--fs-h1` | 31 / 37 px | 700 | нула | заглавия |
| `--fs-h2` | 24 / 31 px | 600 | нула | заглавия |
| `--fs-h3` | 19 / 27 px | 600 | нула | заглавия |
| `--fs-h4` | 15 / 22 px | 600 | нула | заглавия |
| `--fs-h5` | 14 / 21 px | 600 | нула | заглавия |
| `--fs-body` | 13 / 20 px | 400 | нула | основен |
| `--fs-body-sm` | 12 / 18 px | 400 | нула | основен |
| `--fs-input` | 14 / 20 px | 400 | нула | основен |
| `--fs-caption` | 11 / 16 px | 400 | нула | основен |
| `--fs-micro` | 11 / 16 px | 600 | 0.44 px | основен |
| `--fs-th` | 11 / 15 px | 600 | 0.33 px | основен |
| `--fs-mono` | 12 / 18 px | 400 | нула | кодове |
| `--fs-metric` | 26 / 30 px | 600 | нула | основен |

`th` и `micro` се пишат с главни букви. Водещото на `h1` и `h2` е вдигнато спрямо 
базовата стълба, защото българското мастило (Й, Ѝ, у, д, р) е по-високо от em-а и 
при 48/48 се реже.

---

## 3. `theme.css`, целият

Сложете го като първи стилов файл на проекта. Работи и без build стъпка. 
Тъмната тема се вдига с `data-theme="dark"` върху `<html>`; светлата е по 
подразбиране и не следва системната настройка (нарочно, решението е записано).

```css
/* CloudCart Admin Design System · theme.css
 * Проект: Демо Магазин
 * Клиент: без лого · семе #8D58E0 · шрифтова система Montserrat · регистър админ
 * Генерирано: 08.08.2026 от playground-а на дизайн системата. Версия на системата 1.0, токени tokens/base.json.
 *
 * Пуска се както е: няма build стъпка, няма зависимости, няма външни заявки.
 * Тъмната тема се вдига с data-theme="dark" на <html>, светлата е по подразбиране.
 *
 * ШРИФТОВИ ФАЙЛОВЕ. Свалете ги и ги подрежете сами, не ползвайте CDN на Google:
 *   Montserrat (sans, headings, mono)
 *     свалете Montserrat[wght].ttf от https://fonts.google.com/specimen/Montserrat · лиценз OFL-1.1
 *     запишете като /fonts/montserrat-var.woff2  (~95 KB подрязан)
 *   Командата за подрязване (pyftsubset, пази locl и ssNN): docs/FONT-SYSTEMS.md §3.4
 */

@font-face {
  font-family: "Montserrat";
  src: url("/fonts/montserrat-var.woff2") format("woff2-variations");
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}

:root {
  /* --- семе и генерирано семейство (11 стъпки, OKLCH) --- */
  --seed-brand: #8D58E0;
  --brand-50: #F6F3FF;
  --brand-100: #ECE5FF;
  --brand-200: #DED1FF;
  --brand-300: #C9B1FF;
  --brand-400: #AE82FF;
  --brand-500: #9D67F4;
  --brand-600: #8D58E0;   /* котва: най-близката стъпка до семето */
  --brand-700: #7344BB;
  --brand-800: #603A9A;
  --brand-900: #503380;
  --brand-950: #2A1648;

  /* --- основни роли --- */
  --general-background: #F4F5F9;
  --general-foreground: #24252D;
  --general-primary: #7344BB;
  --general-primary-foreground: #FFFFFF;
  --general-secondary: #EBEDF4;
  --general-secondary-foreground: #1A1A2B;
  --general-accent: #EBEDF4;
  --general-accent-foreground: #716E94;
  --general-muted: #EBEDF4;
  --general-muted-foreground: #585F71;
  --general-destructive: #E91A19;
  --general-border: #DBDEEA;
  --general-input: #FFFFFF;

  /* --- карти --- */
  --card-card: #FFFFFF;
  --card-card-foreground: #24252D;

  /* --- изскачащи слоеве --- */
  --popover-popover: #FFFFFF;
  --popover-popover-foreground: #24252D;

  /* --- добавени от нас (unofficial) --- */
  --unofficial-foreground-alt: #716E94;
  --unofficial-body-background: #FFFFFF;
  --unofficial-destructive-border: #FC4F4E;
  --unofficial-destructive-subtle: #FFF1F1;
  --unofficial-contrast-deprecated: #000000;
  --unofficial-backdrop: #33415599;
  --unofficial-mid-deprecated: #9A9BBF;
  --unofficial-mid-alt: #8380AB;
  --unofficial-destructive-foreground: #C51110;
  --unofficial-ghost-foreground: #6D758A;
  --unofficial-ghost: #FFFFFF00;
  --unofficial-ghost-hover: #0000000D;
  --unofficial-primary-hover: #9D67F4;
  --unofficial-secondary-hover: #F4F5F9;
  --unofficial-outline: #FFFFFF1A;
  --unofficial-outline-hover: #33415508;
  --unofficial-outline-active: #3341550D;
  --unofficial-accent-0: #F4F5F9;
  --unofficial-accent-1: #EBEDF4;
  --unofficial-accent-2: #DBDEEA;
  --unofficial-accent-3: #C5C9DC;
  --unofficial-border-0: #F4F5F9;
  --unofficial-border-1: #EBEDF4;
  --unofficial-border-3: #C5C9DC;
  --unofficial-border-4: #AEB1CD;
  --unofficial-border-5: #9A9BBF;
  --unofficial-border-primary: #7344BB;
  --unofficial-success: #D5F6E3;
  --unofficial-success-foreground: #06281E;
  --unofficial-warning: #FEF9C3;
  --unofficial-warning-foreground: #422006;
  --unofficial-error: #FFE0E0;
  --unofficial-error-foreground: #490606;

  /* --- фокус --- */
  --focus-ring: #9D67F4;
  --focus-ring-error: #FC4F4E;

  /* --- странична лента --- */
  --sidebar-sidebar: #EBEDF4;
  --sidebar-sidebar-foreground: #716E94;
  --sidebar-sidebar-accent: #DBDEEA;
  --sidebar-sidebar-accent-foreground: #1A1A2B;
  --sidebar-sidebar-primary: #7344BB;
  --sidebar-sidebar-primary-foreground: #F4F5F9;
  --sidebar-sidebar-border: #C5C9DC;
  --sidebar-sidebar-ring: #9D67F4;
  --sidebar-unofficial-sidebar-muted: #9A9BBF;
  --sidebar-unofficial-avatar: #2A1648;
  --sidebar-unofficial-avatar-foreground: #ECE5FF;

  /* --- графики --- */
  --chart-legacy-chart-1: #9D67F4;
  --chart-legacy-chart-2: #FC6665;
  --chart-legacy-chart-3: #615FFF;
  --chart-legacy-chart-4: #5D0EC0;
  --chart-legacy-chart-5: #ED6BFF;
  --chart-area-orange-fill: #FDD09CB3;
  --chart-area-orange-fill-2: #F8B07EB3;
  --chart-area-orange-stroke: #FFB86A;
  --chart-area-orange-stroke-2: #FF6900;
  --chart-area-blue-fill: #BFDEFFB3;
  --chart-area-blue-stroke: #8EC5FF;
  --chart-area-blue-fill-2: #AACCFFB3;
  --chart-area-blue-stroke-2: #3F8DFF;
  --chart-area-green-fill: #B9FBD2B3;
  --chart-area-green-stroke: #7BF1AB;
  --chart-area-green-fill-2: #82E2A9B3;
  --chart-area-green-stroke-2: #19D163;
  --chart-area-rose-fill: #FFD9DEB3;
  --chart-area-rose-stroke: #FFA1AD;
  --chart-area-rose-fill-2: #F491A8B3;
  --chart-area-rose-stroke-2: #FF4F79;
  --chart-area-teal-fill: #A9F4E8B3;
  --chart-area-teal-stroke: #46EDD5;
  --chart-area-teal-fill-2: #7CE7DCB3;
  --chart-area-teal-stroke-2: #07C0AC;
  --chart-area-purple-fill: #F0E0FFB3;
  --chart-area-purple-stroke: #DAB2FF;
  --chart-area-purple-fill-2: #DEB5FFB3;
  --chart-area-purple-stroke-2: #C67EFF;
  --chart-area-amber-fill: #FFEDACB3;
  --chart-area-amber-stroke: #FFD230;
  --chart-area-amber-fill-2: #FED699B3;
  --chart-area-amber-stroke-2: #FE9A00;
  --chart-static-blue-1: #8EC5FF;
  --chart-static-rose-1: #FFA1AD;
  --chart-static-rose-2: #FF2056;
  --chart-static-rose-3: #EC003F;
  --chart-static-rose-4: #C70036;
  --chart-static-rose-5: #A50036;
  --chart-static-purple-1: #DAB2FF;
  --chart-static-purple-2: #AD46FF;
  --chart-static-purple-3: #9810FA;
  --chart-static-purple-4: #8200DB;
  --chart-static-purple-5: #6E11B0;
  --chart-static-orange-1: #FFB86A;
  --chart-static-orange-2: #FF6900;
  --chart-static-orange-3: #F54A00;
  --chart-static-orange-4: #CA3500;
  --chart-static-orange-5: #9F2D00;
  --chart-static-teal-1: #46EDD5;
  --chart-static-teal-2: #00BBA7;
  --chart-static-teal-3: #009689;
  --chart-static-teal-4: #00786F;
  --chart-static-teal-5: #005F5A;
  --chart-static-blue-2: #2B7FFF;
  --chart-static-blue-3: #155DFC;
  --chart-static-blue-4: #1447E6;
  --chart-static-blue-5: #193CB8;
  --chart-static-amber-1: #FFD230;
  --chart-static-amber-2: #FE9A00;
  --chart-static-amber-3: #E17100;
  --chart-static-amber-4: #BB4D00;
  --chart-static-amber-5: #973C00;
  --chart-static-green-1: #7BF1A8;
  --chart-static-green-2: #00C951;
  --chart-static-green-3: #00A63E;
  --chart-static-green-4: #008236;
  --chart-static-green-5: #016630;

  /* --- obra-shadn-docs --- */
  --obra-shadn-docs-obra-shadcn-ui-docs-1: #FFFFFF;
  --obra-shadn-docs-obra-shadcn-ui-docs-2: #FFFFFF;

  /* --- разстояния, радиуси, сенки (от tokens/base.json, еднакви за всички продукти) --- */
  --space-3xs: 2px;
  --space-2xs: 4px;
  --space-xs: 8px;
  --space-md: 16px;
  --space-lg: 20px;
  --space-xl: 24px;
  --space-2xl: 32px;
  --space-3xl: 40px;
  --space-4xl: 48px;
  --space-5xl: 64px;
  --space-abs-0: 0px;
  --space-abs-0-5: 2px;
  --space-abs-1: 4px;
  --space-abs-1-5: 6px;
  --space-abs-2: 8px;
  --space-abs-2-5: 10px;
  --space-abs-3: 12px;
  --space-abs-3-5: 14px;
  --space-abs-4: 16px;
  --space-abs-5: 20px;
  --space-abs-6: 24px;
  --space-abs-7: 28px;
  --space-abs-8: 32px;
  --space-abs-9: 36px;
  --space-abs-10: 40px;
  --space-abs-11: 44px;
  --space-abs-12: 48px;
  --space-abs-14: 56px;
  --space-abs-16: 64px;
  --space-abs-20: 80px;
  --space-abs-24: 96px;
  --space-abs-28: 112px;
  --space-abs-32: 128px;
  --space-abs-36: 144px;
  --space-abs-40: 160px;
  --space-abs-44: 176px;
  --space-abs-48: 192px;
  --space-abs-52: 208px;
  --space-abs-56: 224px;
  --space-abs-60: 240px;
  --space-abs-64: 256px;
  --space-abs-72: 288px;
  --space-abs-80: 320px;
  --space-abs-96: 384px;
  --space-abs-infinite: 9999px;
  --radius-none: 0px;
  --radius-xs: 2px;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-3xl: 24px;
  --radius-full: 9999px;
  --shadow-2xs: 0px 1px 0px 0px #1A1A2B0D;
  --shadow-xs: 0px 1px 2px 0px #1A1A2B0D;
  --shadow-sm: 0px 1px 3px 0px #1A1A2B1A,0px 1px 2px -1px #1A1A2B1A;
  --shadow-md: 0px 4px 6px -1px #1A1A2B1A,0px 2px 4px -2px #1A1A2B1A;
  --shadow-lg: 0px 10px 15px -3px #1A1A2B1A,0px 4px -4px 6px #1A1A2B1A;
  --shadow-xl: 0px 20px 25px -5px #1A1A2B1A,0px 8px -6px 10px #1A1A2B1A;
  --shadow-2xl: 0px 25px 50px 12px #1A1A2B40;

  /* --- типография: Montserrat, регистър админ --- */
  --font-sans: "Montserrat", system-ui, sans-serif;
  --font-headings: "Montserrat", var(--font-sans);
  --font-mono: "Montserrat", system-ui, sans-serif;
  --fs-micro: 11px;
  --lh-micro: 16px;
  --fw-micro: 600;
  --ls-micro: 0.44px;
  --fs-caption: 11px;
  --lh-caption: 16px;
  --fw-caption: 400;
  --ls-caption: 0px;
  --fs-body-sm: 12px;
  --lh-body-sm: 18px;
  --fw-body-sm: 400;
  --ls-body-sm: 0px;
  --fs-body: 13px;
  --lh-body: 20px;
  --fw-body: 400;
  --ls-body: 0px;
  --fs-input: 14px;
  --lh-input: 20px;
  --fw-input: 400;
  --ls-input: 0px;
  --fs-th: 11px;
  --lh-th: 15px;
  --fw-th: 600;
  --ls-th: 0.33px;
  --fs-h1: 31px;
  --lh-h1: 37px;
  --fw-h1: 700;
  --ls-h1: 0px;
  --fs-h2: 24px;
  --lh-h2: 31px;
  --fw-h2: 600;
  --ls-h2: 0px;
  --fs-h3: 19px;
  --lh-h3: 27px;
  --fw-h3: 600;
  --ls-h3: 0px;
  --fs-h4: 15px;
  --lh-h4: 22px;
  --fw-h4: 600;
  --ls-h4: 0px;
  --fs-h5: 14px;
  --lh-h5: 21px;
  --fw-h5: 600;
  --ls-h5: 0px;
  --fs-mono: 12px;
  --lh-mono: 18px;
  --fw-mono: 400;
  --ls-mono: 0px;
  --fs-metric: 26px;
  --lh-metric: 30px;
  --fw-metric: 600;
  --ls-metric: 0px;
  --font-th: var(--font-sans);
  --fs-body-phone: max(15px, 13px);
  --logo-h: 32px;

  /* --- движение (DESIGN-BRIEF §2) --- */
  --dur-fast: 100ms;
  --dur-base: 160ms;
  --dur-slow: 240ms;
  --ease: cubic-bezier(0.19, 0.91, 0.38, 1);

  /* --- плътност на таблиците: превключвателят в лентата сменя само --row-h.
     --row-h е под (в таблица height действа като min-height), а --row-pad-y е
     вертикалното поле на клетката: ред с два реда съдържание расте и диша,
     вместо съдържанието да опре в ръба. --- */
  --row-h: 44px;
  --row-pad-y: 6px;
}

/* Тъмната тема е преизчислена, не обърната. Всеки тон има своя стойност. */
[data-theme="dark"] {
  /* --- основни роли --- */
  --general-background: #0A0A14;
  --general-foreground: #F7F8F8;
  --general-primary: #AE82FF;
  --general-primary-foreground: #1A1A2B;
  --general-secondary: #34314E;
  --general-secondary-foreground: #EBEDF4;
  --general-accent: #34314E;
  --general-accent-foreground: #C5C9DC;
  --general-muted: #1A1A2B;
  --general-muted-foreground: #8C93A4;
  --general-destructive: #FF6867;
  --general-border: #34314E;
  --general-input: #FFFFFF0D;

  /* --- карти --- */
  --card-card: #1A1A2B;
  --card-card-foreground: #F7F8F8;

  /* --- изскачащи слоеве --- */
  --popover-popover: #1A1A2B;
  --popover-popover-foreground: #F7F8F8;

  /* --- добавени от нас (unofficial) --- */
  --unofficial-foreground-alt: #C5C9DC;
  --unofficial-body-background: #0A0A14;
  --unofficial-destructive-border: #FC4F4E;
  --unofficial-destructive-subtle: #490606;
  --unofficial-contrast-deprecated: #FFFFFF;
  --unofficial-backdrop: #00000099;
  --unofficial-mid-deprecated: #9A9BBF;
  --unofficial-mid-alt: #AEB1CD;
  --unofficial-destructive-foreground: #FF6867;
  --unofficial-ghost-foreground: #DBDEEA;
  --unofficial-ghost: #FFFFFF00;
  --unofficial-ghost-hover: #FFFFFF1A;
  --unofficial-primary-hover: #C9B1FF;
  --unofficial-secondary-hover: #1A1A2B;
  --unofficial-outline: #FFFFFF0D;
  --unofficial-outline-hover: #FFFFFF1A;
  --unofficial-outline-active: #FFFFFF26;
  --unofficial-accent-0: #34314E;
  --unofficial-accent-1: #1A1A2B;
  --unofficial-accent-2: #34314E;
  --unofficial-accent-3: #716E94;
  --unofficial-border-0: #0A0A14;
  --unofficial-border-1: #1A1A2B;
  --unofficial-border-3: #716E94;
  --unofficial-border-4: #8380AB;
  --unofficial-border-5: #9A9BBF;
  --unofficial-border-primary: #AE82FF;
  --unofficial-success: #7BDAAD;
  --unofficial-success-foreground: #06281E;
  --unofficial-warning: #FEF08A;
  --unofficial-warning-foreground: #422006;
  --unofficial-error: #FFA09F;
  --unofficial-error-foreground: #490606;

  /* --- фокус --- */
  --focus-ring: #C9B1FF;
  --focus-ring-error: #FF6867;

  /* --- странична лента --- */
  --sidebar-sidebar: #1A1A2B;
  --sidebar-sidebar-foreground: #C5C9DC;
  --sidebar-sidebar-accent: #34314E;
  --sidebar-sidebar-accent-foreground: #EBEDF4;
  --sidebar-sidebar-primary: #AE82FF;
  --sidebar-sidebar-primary-foreground: #1A1A2B;
  --sidebar-sidebar-border: #34314E;
  --sidebar-sidebar-ring: #C9B1FF;
  --sidebar-unofficial-sidebar-muted: #9A9BBF;
  --sidebar-unofficial-avatar: #C9B1FF;
  --sidebar-unofficial-avatar-foreground: #2A1648;

  /* --- графики --- */
  --chart-legacy-chart-1: #AE82FF;
  --chart-legacy-chart-2: #E56867;
  --chart-legacy-chart-3: #5558F2;
  --chart-legacy-chart-4: #682DB2;
  --chart-legacy-chart-5: #C84CD9;
  --chart-area-orange-fill: #755738B3;
  --chart-area-orange-fill-2: #76380EB3;
  --chart-area-orange-stroke: #FFB86A;
  --chart-area-orange-stroke-2: #FF7915;
  --chart-area-blue-fill: #475D75B3;
  --chart-area-blue-stroke: #8EC5FF;
  --chart-area-blue-fill-2: #1F4176B3;
  --chart-area-blue-stroke-2: #539BFF;
  --chart-area-green-fill: #3F6E51B3;
  --chart-area-green-stroke: #7BF1A8;
  --chart-area-green-fill-2: #0E5E2EB3;
  --chart-area-green-stroke-2: #19D163;
  --chart-area-rose-fill: #754E53B3;
  --chart-area-rose-stroke: #FFA1AD;
  --chart-area-rose-fill-2: #741B30B3;
  --chart-area-rose-stroke-2: #FF4670;
  --chart-area-teal-fill: #409388B3;
  --chart-area-teal-stroke: #46EDD5;
  --chart-area-teal-fill-2: #0E5951B3;
  --chart-area-teal-stroke-2: #1CCFB9;
  --chart-area-purple-fill: #655576B3;
  --chart-area-purple-stroke: #DAB2FF;
  --chart-area-purple-fill-2: #532A77B3;
  --chart-area-purple-stroke-2: #A96ADD;
  --chart-area-amber-fill: #746221B3;
  --chart-area-amber-stroke: #FFD230;
  --chart-area-amber-fill-2: #734B0EB3;
  --chart-area-amber-stroke-2: #FFA50A;
  --chart-static-blue-1: #8EC5FF;
  --chart-static-rose-1: #FFA1AD;
  --chart-static-rose-2: #FF2056;
  --chart-static-rose-3: #EC003F;
  --chart-static-rose-4: #C70036;
  --chart-static-rose-5: #A50036;
  --chart-static-purple-1: #DAB2FF;
  --chart-static-purple-2: #AD46FF;
  --chart-static-purple-3: #9810FA;
  --chart-static-purple-4: #8200DB;
  --chart-static-purple-5: #6E11B0;
  --chart-static-orange-1: #FFB86A;
  --chart-static-orange-2: #FF6900;
  --chart-static-orange-3: #F54A00;
  --chart-static-orange-4: #CA3500;
  --chart-static-orange-5: #9F2D00;
  --chart-static-teal-1: #46EDD5;
  --chart-static-teal-2: #00BBA7;
  --chart-static-teal-3: #009689;
  --chart-static-teal-4: #00786F;
  --chart-static-teal-5: #005F5A;
  --chart-static-blue-2: #2B7FFF;
  --chart-static-blue-3: #155DFC;
  --chart-static-blue-4: #1447E6;
  --chart-static-blue-5: #193CB8;
  --chart-static-amber-1: #FFD230;
  --chart-static-amber-2: #FE9A00;
  --chart-static-amber-3: #E17100;
  --chart-static-amber-4: #BB4D00;
  --chart-static-amber-5: #973C00;
  --chart-static-green-1: #7BF1A8;
  --chart-static-green-2: #00C951;
  --chart-static-green-3: #00A63E;
  --chart-static-green-4: #008236;
  --chart-static-green-5: #016630;

  /* --- obra-shadn-docs --- */
  --obra-shadn-docs-obra-shadcn-ui-docs-1: #111628;
  --obra-shadn-docs-obra-shadcn-ui-docs-2: #201D1B;
}

/* --- основа. Дотук са само стойности; оттук нататък са трите правила,
   които всеки продукт на системата дължи. --- */

html {
  font-family: var(--font-sans);
  font-size: var(--fs-body);
  line-height: var(--lh-body);
  color: var(--general-foreground);
  background: var(--general-background);
  /* задължително: иначе цените в колона подскачат */
  font-variant-numeric: tabular-nums lining-nums;
}

:is(h1, h2, h3, h4, h5) { font-family: var(--font-headings); }
h1 { font-size: var(--fs-h1); line-height: var(--lh-h1); font-weight: var(--fw-h1); letter-spacing: var(--ls-h1); }
h2 { font-size: var(--fs-h2); line-height: var(--lh-h2); font-weight: var(--fw-h2); letter-spacing: var(--ls-h2); }
h3 { font-size: var(--fs-h3); line-height: var(--lh-h3); font-weight: var(--fw-h3); letter-spacing: var(--ls-h3); }
h4 { font-size: var(--fs-h4); line-height: var(--lh-h4); font-weight: var(--fw-h4); }
h5 { font-size: var(--fs-h5); line-height: var(--lh-h5); font-weight: var(--fw-h5); }

/* данните живеят без лигатури: „->“ и „!=“ вътре в SKU трябва да оцелеят */
:is(td, th, .sku, .mono, input, code, .num) {
  font-variant-ligatures: none;
  font-feature-settings: "liga" 0, "calt" 0, "dlig" 0;
}
.mono, .sku, code { font-family: var(--font-mono); font-style: normal; }

/* една идиома за фокус, навсякъде, без изключения */
:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

/* отвореният списък на select е на системата, не на ОС (Chrome 135+;
   по-стар браузър тихо остава на родния изглед) */
select, ::picker(select) { appearance: base-select; }
/* base-select маха родното центриране: бутонът е флекс кутия */
select { display: inline-flex; align-items: center; }
::picker(select) {
  margin-top: 4px;
  background: var(--popover-popover);
  color: var(--popover-popover-foreground);
  border: 1px solid var(--general-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: 4px;
}
option { display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: var(--radius-sm); }
option:hover, option:focus { background: var(--unofficial-accent-0); }
option:checked { color: var(--general-primary); font-weight: 600; }
select::picker-icon { margin-left: auto; color: var(--general-muted-foreground); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 4. Проверка, преди да кажете „готово“

Минете списъка сами, екран по екран, и докладвайте резултата:

- [ ] Йерархията се чете и с изключени рамки?
- [ ] Мрежата е 4 px, а композицията диша (карта 20, между карти 20 до 24, секции 
      32 до 40)?
- [ ] Марковият цвят е точно на шестте позволени места, а хромът е сив?
- [ ] Числата са отдясно и наистина равни по ширина — измерете „1“ срещу „0“, 
      не се доверявайте на `tabular-nums` сама по себе си; празната клетка е „–“?
- [ ] Няма декоративни сенки, няма движение при посочване, няма дълго тире, няма емоджи?
- [ ] Всяка контрола има посочване, натискане, фокус и забрана; целите са поне 24 px 
      (44 при докосване)?
- [ ] Фокус пръстенът е видим навсякъде и е една и съща идиома?
- [ ] Контрастът на новите двойки е поне AA (4.5 за текст, 3.0 за фокус и за рамка, 
      която е единственият знак, че полето е поле)?
- [ ] Тъмната тема е проверена, особено тонираните значки?
- [ ] `prefers-reduced-motion` е зачетено?
- [ ] Български: Вие-форма, дати `24.07.2026`, числа `1 240,50 лв.`, `<html lang="bg">`?
- [ ] Проверено на трите ширини: 1280, 768 и 390?
- [ ] Никоя стойност в стиловете не е сурова там, където има токен?

---

## 5. Този случай: съществуващ проект

Продуктът вече работи и някой го е писал внимателно. Задачата не е пренаписване, 
а привеждане към една система. Посоката на дизайна остава, каквато е; повечето 
препоръки местят стойност с не повече от 2 px или не местят нищо.

### Стъпка 1. Първо одит, преди да е пипнат кой да е ред

Не променяйте нищо, докато не изкарате отчет и не го покажете на човек. Отчетът 
изброява, по файлове и с числа:

- колко сурови `font-size`, `padding`, `margin`, `gap`, `border-radius` има и кои 
  са петте най-чести стойности (те показват коя стълба липсва),
- кои цветове са извън темата и колко пъти се срещат,
- къде марковият цвят излиза извън шестте позволени места,
- сенки върху неплаващи елементи,
- места с махнат фокус пръстен (`outline: none` без замяна),
- дълги тирета и емоджи в интерфейсни низове — включително в тези, които се 
  сглобяват в JavaScript,
- хоризонтално преливане на телефон (320 / 390 / 430): сравнете `innerWidth` и 
  `scrollWidth` с ширината на устройството. Преливането не е козметика — Chrome 
  смалява страницата и изнася фиксирания хром под видимото поле,
- дати и числа в невярен формат, английски низове в български екран,
- шрифта: има ли двоичният файл български език изобщо. Проверява се със скрипт 
  върху файла, не по репутация. Наш продукт е пускал Roboto на българска 
  аудитория месеци наред, а той няма нито един `cyrl` език и всеки екран е 
  изписвал руски форми.

Отчетът завършва с изречение „ето какво се разминава и колко струва всяко“, а не 
с готови промени. Изчаквате решение.

### Стъпка 2. Слой за съвместимост, не един голям комит

Хиляда реда ръчно писан стил не се сменят с един комит: това е неприемливо за 
пускане и никой не може да го прегледа. Редът е:

1. слагате `theme.css` пръв, без да пипате нищо друго. Нищо не трябва да се счупи, 
   защото още никой не ползва променливите;
2. добавяте тънък `compat.css`, който картира съществуващите имена на класове към 
   новите променливи (`.wui-card { background: var(--card-card); border-color: 
   var(--general-border); }`). Оттук нататък целият продукт вече взима цветовете 
   си от темата и тъмната тема тръгва наведнъж;
3. минавате екран по екран, пренаписвате го на токени и триете съответните 
   правила от `compat.css`. Всеки екран е отделен комит, който може да се върне 
   сам.

### Стъпка 3. Суровите стойности стават токени, без „почти“

Ако кодът ползва 15 px, а стълбата има 14, стойността става 14 и това се записва 
в отчета. Не се въвежда нов токен, за да пасне на стар навик; и не се оставя 
сурова стойност, „защото е само на едно място“. Стълба, която не покрива реалната 
употреба, си гарантира изоставянето: затова разликите се изброяват, а не се 
заобикалят.

### Мерките, към които се привежда всеки екран

Същият речник, с който системата е рисувана. При одита той е еталонът, спрямо 
който се мери всяко разминаване; при пренаписването екран по екран е целта. 
Не измисляйте размер и отстояние, които този списък вече дава:

| Компонент | Правило |
|---|---|
| Бутони | височини 28 (плътен) / 32 (по подразбиране) / 40 (голям), хоризонтално поле съответно 12 / 14 / 20 px: надписът никога не опира рамката. Икона 16 px на 6 px от текста. Основен, вторичен (повърхност и рамка), безрамков, опасен (червено само за трудно обратими действия). Един основен бутон на страница или карта. |
| Полета | височина 32 (40 на екрана за вход), етикет отгоре, изречен регистър, до три думи. Ширини от стълбата 104 / 216 / 328 / 440 / 552, никога 100 % по подразбиране. Файловото поле никога не остава с браузърския вид: `::file-selector-button` се стилизира като компактния вторичен бутон, името на файла е приглушено. Отвореният списък на select също е на системата: theme.css носи `appearance: base-select` и стилизиран `::picker(select)` върху popover токените (Chrome 135+; по-стар браузър тихо остава на родния изглед). Кутийките и радиобутоните носят марковия тон през `accent-color`, зададен глобално, а не по компонент: родното синьо е чужд цвят в палитрата и на 20 px на телефон е невъзможно да се пропусне. |
| Таблици | ред 44 px по подразбиране, превключвател 36 / 44 / 52 в лентата, залепен заглавен ред 40 px. Височината на реда е под, не таван: клетката носи и 6 px вертикално поле (`--row-pad-y`), така че ред с два реда съдържание (име + код, значка + метър) расте и диша, вместо съдържанието да опре в ръба. Числата отдясно и табулирани, кодовете отляво, в шрифта на системата, с изгасени лигатури; отделен моноширинен няма. Само сортираната колона показва иконата си. Избор на редове сменя заглавния ред с лента за масови действия на място. Имена на хора и кодове не се пренасят на втори ред: колоната се разширява (white-space: nowrap). Страниране долу вдясно (25/50/100, по подразбиране 50), никога безкрайно превъртане. Под 768 px СПИСЪЧНАТА таблица става карти на редове, а числовата решетка (бонуси, матрици) НЕ става: тя скролва настрани със закотвена и ограничена по ширина първа колона. Дълга стойност в клетка иска `overflow-wrap: anywhere` (не `break-word`). |
| Списъчна страница | заглавие (име, брой, действия), после записаните изгледи и бързите филтри като редица бутони (28 px, радиус md, видима рамка в покой, активният с 10 до 12 % марков тон; табове има само за раздели на съдържание, никога за филтри), после търсене, филтри и подредба, после чипове с приложените филтри и „Изчисти всички“, после таблицата и страницирането. Ритъмът по вертикала: 16 px под табовете, 8 px между реда с търсенето и чиповете, 16 px преди таблицата. Лента с филтри никога не лепне за рамка: ако филтрите живеят в карта, полето на картата е поне 16 px от всички страни, включително отгоре. Състоянието на филтрите винаги стои в URL-а. |
| Плочки (KPI) | стойност с табулирани цифри от семейството за заглавия. Стойността никога не излиза от плочката и никога не я разширява: дълга стойност смалява кегела си и остава на ЕДИН ред (fit-to-width с няколко реда JS; преносът е само резервът без JS), min-width: 0 върху плочката, височината не мърда (line-height е в px). Без цветни акцентни ленти по ръба на плочка или карта (горе или отстрани): акцентът живее в съдържанието, като точка, значка или оцветен текст. |
| Графики | цветовете идват само от chart токените, никакво сурово шестнадесетично в конфигурацията. За големи запълвания (резени на поничка, стълбове) пастелният ред `--chart-static-*-1`; наситените редове са за тънки линии и малки маркери. Резенът на статус носи нюанса на своята значка. Мрежата е `--unofficial-border-1`, надписите `--general-muted-foreground`, шрифтът е шрифтът на системата. Конфигурацията е фабрика, която чете токените при построяване, и се преизчислява при смяна на темата. |
| Формуляри | Бързи стойности под поле (например месечните бутони под датите) стоят на 12 px под контролата, никога залепени. 32 px между полетата (24 в панели), 48 px преди групата бутони. Форматните полета се проверяват при напускане, останалите при изпращане. Грешката стои под полето и е конкретна. Бутонът за изпращане не се забранява, за да изрази невалидност. При промени изплува лента „Незапазени промени“ с Отказ и Запази. |
| Значки за статус | тониран фон плюс наситен текст, без водеща точка или икона пред надписа (решение от 07.08.2026). Статусът никога не се носи само от цвят: изписаният текст е задължителен. Тъмната тема получава свои стойности, не изсветлени светли. ВСЕКИ мини-индикатор в таблица (брояч, задържане, процент) носи същата форма: 20 px височина, радиус sm, 11 px/600; пил в таблица няма. |
| Навигация | странична лента 240 px разгъната, 64 px релса, състоянието се помни. Елемент 36 px, икона 20 px. Активният е тон плюс марков текст. Секции с надписи от 11 px главни букви. Най-много две нива, третото са табове в страницата. Горна лента 48 до 56 px с търсене, известия и потребител, а превключвателят на магазин винаги най-вдясно. На 64-те пиксела на релсата няма място за словесен знак: ако продуктът няма квадратна марка, свийте знака по ШИРИНА с `height: auto` (фиксирана височина го реже). Под 768 px чекмедже плюс долна лента, породени от един списък; чекмеджето затваря при затъмнение, `Escape`, плъзгане наляво, връща фокуса и пуска заключения скрол при преминаване над границата. |
| Панели и слоеве | затвореният панел, чекмедже или лист излиза от ПОТОКА (`display: none`), а не само се измества с `transform`: изместеният слой остава напълно оформен и екран, който ражда по един панел на ред, убива мобилния рендер. Плъзгането се пази на две стъпки (клас за анимация → принуден reflow → `.open`), а затварянето сваля класа на `transitionend` с резервен таймер заради `prefers-reduced-motion`. На телефон панелът е цял екран. |
| Обратна връзка | кратко известие долу вдясно за рутинното (до три думи, 5 секунди, никога за грешки), банер в потока за постоянното, грешката на полето под полето. Скелетите повтарят подредбата. Под 1 секунда не се показва нищо, над 10 секунди задачата отива във фонов процес. |

### Стъпка 4. Какво не се пипа

Функциите на продукта, информационната архитектура, имената на маршрутите, 
данните и текстовете остават. Тази задача сменя как изглежда, не какво прави. 
Ако смятате, че някой поток е сбъркан, напишете го в отчета отделно и продължете 
с привеждането.

### Стъпка 5. Как се докладва

За всеки екран: какво е било, какво става, кои токени влизат, колко правила са 
изтрити от `compat.css` и какво остава. Накрая минете списъка от §4 и кажете 
честно кое не сте проверили.

