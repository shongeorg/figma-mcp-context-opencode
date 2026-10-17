# GreenShop — Laravel-бекенд магазину

Серверна частина магазину GreenShop: класичний SSR на Blade поверх вже готової
статичної верстки (Figma → HTML/CSS). Без SPA-обв'язки магазину — увесь інтерфейс
магазину це Blade-шаблони, Fortify відповідає за аутентифікацію, а наявний
Inertia/Vue starter-kit залишений лише для сторінок `/settings/*`.

Гілка `e-commerce`. Гілка `main` — недоторкана статична верстка.

---

## Зміст

- [Стек](#стек)
- [Швидкий старт](#швидкий-старт)
- [Дані та міграції](#дані-та-міграції)
- [Схема бази даних](#схема-бази-даних)
- [Маршрути](#маршрути)
- [Сервісний шар](#сервісний-шар)
- [Кошик](#кошик)
- [Каталог: фільтри, сортування, пагінація](#каталог-фільтри-сортування-пагінація)
- [Оформлення замовлення](#оформлення-замовлення)
- [Зображення товарів](#зображення-товарів)
- [Адмін-панель](#адмін-панель)
- [Аутентифікація та профіль](#аутентифікація-та-профіль)
- [Сідинги та тестові акаунти](#сідинги-та-тестові-акаунти)
- [Структура проєкту](#структура-проєкту)
- [Тести, стайл-чеки](#тести-стайл-чеки)

---

## Стек

| Шар | Обране |
| --- | --- |
| Фреймворк | Laravel `^13.17` |
| PHP | `^8.3` (локально виконується на PHP 8.5) |
| БД | PostgreSQL (Neon, хостинг у `eu-central-1`) |
| Фронт магазину | Blade + вендорний CSS/JS із верстки (`public/assets`) |
| Аутентифікація | Laravel Fortify `^1.37` (включно з 2FA та passkeys) |
| SSR SPA-частини | Inertia `^3.0` + Vue — тільки `/settings/*` |
| Тести | Pest `^5.3` |
| Форматування / статика | Pint `^1.27`, PHPStan |

Сервер локально піднімає **Laravel Herd** — додаток доступний на
<http://larka.test>. Ручний `artisan serve` не потрібен і не використовується.

---

## Швидкий старт

```bash
cd larka
composer install
npm install
cp .env.example .env
php artisan key:generate
php artisan storage:link
php artisan migrate --seed
npm run build
```

Потрібні змінні середовища (у `.env`):

| Змінна | Призначення |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` | PostgreSQL. Для міграцій використовуй **прямий** endpoint |
| `UNSPLASH_API_KEY` | перший провайдер зображень |
| `PEXELS_API_KEY` | другий провайдер |
| `PIXABAY_API_KEY` | третій провайдер |

> **Про Neon:** пул-ендпоінт (`ep-…-pooler`) ламає prepared statements усередині
> транзакцій, через що міграції падають. Для `php artisan migrate` вказуємо прямий
> хост `ep-…` без `-pooler`. Робочий трафік від додатка може йти через пулер.

---

## Дані та міграції

Одинадцять міграцій (усі в `database/migrations/2026_10_17_*`), застосовані на Neon:

| Міграція | Що робить |
| --- | --- |
| `create_categories_table` | Дерево категорій: `slug`, `name`, `position`, `parent_id` |
| `create_products_table` | Каталог товарів |
| `create_product_images_table` | Галерея товару: `path`, `position` |
| `create_addresses_table` | Збережені адреси користувача |
| `create_coupons_table` | Промокоди: тип `percent`/`fixed`, мінімальна сума, термін |
| `create_orders_table` | Замовлення + JSON `shipping_address` |
| `create_order_items_table` | Позиції зі знімком ціни на момент покупки |
| `create_cart_items_table` | Персистентний кошик залогінених |
| `create_reviews_table` | Відгуки з оцінкою |
| `add_shop_fields_to_users_table` | `role`, `balance` |
| `add_phone_to_users_table` | `phone` |

---

## Схема бази даних

### `products`

| Поле | Тип | Нотатки |
| --- | --- | --- |
| `sku` | string, unique | `GS-00001` … `GS-00040` |
| `category_id` | FK → `categories` | |
| `name`, `slug` | string | `slug` унікальний, використовується в URL |
| `short_description`, `description` | text | |
| `price` | decimal | |
| `old_price` | decimal, nullable | якщо заповнене — товар у розпродажі |
| `discount_percent` | int, nullable | |
| `rating` | decimal | середня оцінка |
| `reviews_count`, `sold_count`, `stock` | int | |
| `is_new` | bool | окрема вкладка каталогу |
| `sizes` | json | `["Small","Medium","Large"]` |

Станові методи моделі: `onSale()` — колонка запиту для знижок.

### `orders`

`number` (`GS-261017-YGKO`), `status`, `payment_method` (`cod` / `card` / `bank`),
`subtotal`, `discount`, `shipping`, `total`, `coupon_code`, `shipping_address`
(JSON), `note`, `placed_at`.

Константи статусів: `STATUS_PENDING`, `STATUS_PROCESSING`, `STATUS_SHIPPED`,
`STATUS_DELIVERED`, `STATUS_CANCELLED`.

Аксесори: `is_cancellable` (лише `pending`/`processing`), `is_paid`,
`status_label`.

`order_items` зберігають знімок товару на момент покупки: `product_name`,
`product_sku`, `image_path`, `unit_price`, `unit_old_price`, `line_total`.

### `users`

Ролі: `User::ROLE_ADMIN`, `User::ROLE_CUSTOMER`. Доступ визначає `isAdmin`.

---

## Маршрути

39 маршрутів поза vendor (`php artisan route:list --except-vendor`).

### Каталог і публічна частина

| Метод | URL | Назва | Контролер |
| --- | --- | --- | --- |
| GET | `/` | `home` | `HomeController` |
| GET | `/shop` | `shop.index` | `ShopController` |
| GET | `/product/{product:slug}` | `product.show` | `ProductController@show` |
| POST | `/product/{product:slug}/reviews` | `reviews.store` | `ProductController@storeReview` |

### Кошик і замовлення

| Метод | URL | Назва |
| --- | --- | --- |
| GET/POST/DELETE | `/cart` | `cart.index` / `cart.store` / `cart.destroy` |
| POST | `/cart/update` | `cart.update` |
| POST / DELETE | `/cart/coupon` | `cart.coupon.apply` / `cart.coupon.remove` |
| GET / POST | `/checkout` | `checkout.show` / `checkout.store` |
| GET | `/orders/{order}` | `orders.show` |
| DELETE | `/orders/{order}` | `orders.cancel` |

### Особистий кабінет

| Метод | URL | Назва |
| --- | --- | --- |
| GET / PUT | `/account` | `account.show` / `account.update` |
| PUT | `/account/password` | `account.password` |
| GET / POST | `/account/addresses` | `account.addresses` / `.store` |
| PUT / DELETE | `/account/addresses/{address}` | `.update` / `.destroy` |
| GET | `/account/orders` | `account.orders` |

### Адмін-панель (`admin` middleware)

| Метод | URL | Назва |
| --- | --- | --- |
| GET | `/admin` | `admin.dashboard` |
| GET / POST | `/admin/products` | `admin.products.index` / `.store` |
| GET | `/admin/products/create` | `admin.products.create` |
| GET / PUT / DELETE | `/admin/products/{product}` | `.edit` / `.update` / `.destroy` |
| GET | `/admin/orders` | `admin.orders.index` |
| PUT | `/admin/orders/{order}/status` | `admin.orders.status` |
| DELETE | `/admin/orders/{order}` | `admin.orders.destroy` |

### `/settings/*` (Inertia + Vue, starter-kit)

`profile.edit` / `profile.update` / `profile.destroy`,
`security.edit` / `user-password.update`, `appearance`,
`.well-known/passkey-endpoints`.

---

## Сервісний шар

Логіка винесена з контролерів у три сервіси.

### `App\Services\CatalogService`

Один публічний метод `data(Request $request, int $perPage = 9): array` повертає
все, що треба сторінці каталогу: пагінатор, категорію з нащадками, активну
вкладку, межі ціни для слайдера та загальну кількість товарів.

### `App\Services\CartService`

`lines()`, `add()`, `updateQuantity()`, `remove()`, `clear()`, `count()`,
`subtotal()`, `mergeSessionToUser()`. Адаптує під гостя та користувача — див.
розділ [Кошик](#кошик).

### `App\Services\ImageSearch\`

| Клас | Роль |
| --- | --- |
| `ImageProvider` | Інтерфейс: `search(string $query, int $count): array<string>` |
| `BaseImageProvider` | Спільна HTTP-обгортка, пагінація, нормалізація URL |
| `UnsplashImageProvider` | перший у ланцюжку |
| `PexelsImageProvider` | другий |
| `PixabayImageProvider` | третій |
| `ProductImageFetcher` | Завантаження файлів на диск і прив'язка до товару |

Реєстрація провайдерів — у `App\Providers\ImageSearchServiceProvider`.

### Спільні дані макета

`App\Providers\AppServiceProvider::shareLayoutData()` — View composer на
`layouts.app`. Він підставляє `$cartCount` та `$footerCategories` у кожен
Blade-шаблон, тому контролери не передають ці змінні самостійно.

---

## Кошик

Гібридна схема:

- **Гість** — корзина живе в сесії: `Session::get('cart', [])`, ключ
  `{productId}|{size}`.
- **Залогінений** — корзина в таблиці `cart_items` (`user_id`, `product_id`,
  `size`, `quantity`).
- **При логіні** — `CartService::mergeSessionToUser()` переносить сесійні позиції
  в базу (`firstOrCreate` + `increment`, тож кількості складаються) і чистить
  сесію.

Один і той самий публічний інтерфейс працює для обох випадків, тож контролери
не знають, де зберігається кошик.

---

## Каталог: фільтри, сортування, пагінація

Усі фільтри — через query string, тому будь-яку комбінацію можна ділитися
посиланням.

| Параметр | Що робить |
| --- | --- |
| `category` | Пошук категорії за `slug` + `descendantsIds()` — підтягує й дочірні категорії |
| `tab` | `all` / `new` / `sale` |
| `q` | Пошук `ilike` по назві та короткому опису |
| `min`, `max` | Діапазон ціни |
| `size` | `whereJsonContains('sizes', …)` |
| `sort` | `default` / `price-asc` / `price-desc` / `name` |

`default` сортує за `is_new` спадно, далі за `id` спадно. Пагінація —
`paginate(9)->withQueryString()`, тож фільтри зберігаються при переході між
сторінками.

---

## Оформлення замовлення

`CheckoutController::store()` виконує все всередині одного `DB::transaction`:

1. Валідація форми: ПІБ, вулиця, місто, регіон, поштовий індекс, телефон,
   email, спосіб оплати (`cod` / `card` / `bank`), примітка.
2. Повторна перевірка промокоду за *поточною* сумою: `Coupon::isValidFor()` та
   `discountFor()` — гостеві не вигідно підмінити суму після застосування коду.
3. Створення `Order` з номером `Order::generateNumber()`.
4. Для кожної позиції — `OrderItem` зі знімком ціни та зображення, зниження
   `stock` і збільшення `sold_count`.
5. `used_count++` для промокоду.

Доставка фіксована — `16.00`. Після комітів кошик і промокод чистяться, користувач
перенаправляється на `orders.show`.

### Скасування та видалення замовлення

- `OrderController::cancel` — клієнт скасовує власне замовлення, доступно лише
  для `pending` і `processing`.
- `Admin\AdminOrderController::destroy` — адмін видаляє, крім `shipped` і
  `delivered`.

Кнопки: `account/orders`, `orders/show`, `admin/orders/index`.

---

## Зображення товарів

Ланцюжок провайдерів: **Unsplash → Pexels → Pixabay**. Якщо перший повернув
порожній список, спробовується наступний.

`ProductImageFetcher::attachToProduct()`:

1. Шукає URL у провайдерів.
2. Завантажує файл через `Http::timeout(30)`.
3. Визначає розширення з `Content-Type` (fallback — з URL, далі `jpg`).
4. Пише на `public`-диск у `products/{slug}/{name}-{index}.{ext}`.
5. Створює запис у `product_images` з `position`.

Помилка завантаження логується як `Log::warning` і не зупиняє сідинг. Посилання
на файли — через `storage:link`.

---

## Адмін-панель

Захищена мідлваром `admin` (аліас у `bootstrap/app.php` →
`App\Http\Middleware\EnsureUserIsAdmin`). Звичайні Blade-CRUD без нових пакетів,
окремий макет `admin/layout` та стилі `public/assets/css/admin.css`.

- **Дашборд** — воронка замовлень, виручка, найпопулярніші товари.
- **Товари** — створення, редагування, видалення, керування стоком.
- **Замовлення** — зміна статусу (`PUT`), видалення.

---

## Аутентифікація та профіль

Fortify з мінімальними правками `config/fortify.php`:

```php
Features::registration(),
Features::resetPasswords(),
Features::twoFactorAuthentication(),
Features::passkeys(),
```

- `home` → `/account`.
- **Верифікація email вимкнена** навмисно — 9 відповідних тестів пропускаються.
- `User` реалізує `FortifyPasskeyUser` і використовує `PasskeyAuthenticatable`.
- `/settings/security` — за `password.confirm`.

Паролі формуються через `PasswordValidationRules` / `ProfileValidationRules`
(`app/Concerns`).

---

## Сідинги та тестові акаунти

`php artisan migrate --seed` викликає `DatabaseSeeder` → `UserSeeder`,
`CategorySeeder`, `ProductSeeder`.

### Акаунти

| Роль | Email | Пароль | Баланс |
| --- | --- | --- | --- |
| Адмін | `admin@admin.test` | `admin` | 0 |
| Клієнт | `user@user.test` | `user` | 250 |

### Дані

- **9 категорій**: House Plants, Potter Plants, Seeds, Small Plants, Big Plants,
  Succulents, Terrariums, Gardening, Accessories.
- **40 товарів** (`GS-00001` … `GS-00040`) з цінами, знижками, рейтингами,
  стоком, розмірами та описами. Станові методи фабрики: `onSale()`, `isNew()`,
  `outOfStock()`.
- **~118 зображень**, завантажених з API провайдерів.
- **2 промокоди**:

| Код | Тип | Значення | Мін. сума | Термін |
| --- | --- | --- | --- | --- |
| `GREEN10` | percent | 10 | 50 | рік |
| `SAVE20` | fixed | 20 | 150 | 6 місяців |

Сідинг ідемпотентний (`updateOrCreate`), тому його можна запускати повторно.

---

## Структура проєкту

```
larka/
├── app/
│   ├── Concerns/                  PasswordValidationRules, ProfileValidationRules
│   ├── Http/
│   │   ├── Controllers/
│   │   │   ├── Admin/             AdminDashboard, AdminOrder, AdminProduct
│   │   │   ├── Settings/          Profile, Security (Inertia)
│   │   │   └── …                  Home, Shop, Product, Cart, Checkout,
│   │   │                          Order, Account, Address
│   │   └── Middleware/            EnsureUserIsAdmin, HandleAppearance, …
│   ├── Models/                    Category, Product, ProductImage, Review,
│   │                              Address, Coupon, Order, OrderItem,
│   │                              CartItem, User
│   ├── Providers/                 AppServiceProvider, ImageSearchServiceProvider
│   └── Services/
│       ├── CartService.php
│       ├── CatalogService.php
│       └── ImageSearch/           6 класів ланцюжка зображень
├── database/
│   ├── factories/                 Category, Product, User (→ admin())
│   ├── migrations/                11 міграцій
│   └── seeders/                   Database, User, Category, Product
├── public/assets/                 css/shop.css, css/admin.css, js/main.js
├── resources/views/               27 Blade-шаблонів
├── routes/                        web.php, settings.php
└── tests/                         Pest, Feature, Unit
```

`resources/views`:

```
account/{show,orders,addresses}     admin/{dashboard,layout}
admin/orders/index                  admin/products/{index,form}
auth/{login,register,forgot-password,reset-password,
     confirm-password,two-factor-challenge}
cart/index                          checkout/show
components/product-card             home
layouts/app                         orders/show
partials/{account-nav,auth-dialogs,catalog,hero}
product/show                        shop/index
```

---

## Тести, стайл-чеки

```bash
php artisan test --compact     # 57 тестів: 48 passed, 9 skipped
vendor/bin/pint --dirty        # форматування PHP
phpstan analyse                # статичний аналіз
```

9 пропущених тестів — верифікація email, фічі вимкнено свідомо.

Стан на момент написання: **57 тестів, 48 passed, 9 skipped, 152 assertions**,
Pest відпрацьовує за ~6 с. Тестова БД — sqlite `:memory:` у `phpunit.xml`, тому
тести ніколи не чіпають Neon.

Покриття існуючими тестами: акаунт і паролі, дашборд, спільні дані макета,
скасування замовлення, Fortify-аутентифікація (логін, реєстрація, скидання
пароля, 2FA, підтвердження пароля), налаштування профілю та безпеки.
