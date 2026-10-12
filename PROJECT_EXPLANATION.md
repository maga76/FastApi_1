# Объяснение проекта Internet Shop API

Этот файл нужен для подготовки к защите проекта. Здесь простыми словами объясняется, что использовано, зачем нужен каждый файл и как работает основной код.

## 1. Что делает проект

Проект — это backend API интернет-магазина. Через него можно:

- создавать пользователей;
- создавать категории и товары;
- искать, фильтровать и сортировать товары;
- добавлять товары в корзину;
- создавать заказ из корзины;
- уменьшать количество товара на складе после заказа;
- отменять заказ и возвращать товар на склад;
- смотреть историю покупок;
- оставлять отзывы и ставить рейтинг;
- добавлять товары в избранное;
- получать статистику магазина.

Авторизации в проекте нет. Поэтому `user_id` передаётся вручную.

## 2. Какие технологии использованы

### FastAPI

FastAPI создаёт API и endpoints. Например:

```python
@app.get("/products/")
def get_products():
    ...
```

`@app.get` означает GET-запрос. Он используется для получения данных.

### SQLAlchemy

SQLAlchemy используется для работы с базой данных через Python-классы.

Вместо ручного SQL:

```sql
SELECT * FROM products;
```

можно написать:

```python
db.query(Product).all()
```

### SQLite

SQLite — простая файловая база данных. Она хранится в файле:

```text
internet_shop.db
```

### Pydantic

Pydantic проверяет входящие данные. Например, цена должна быть больше нуля, stock не может быть отрицательным, а рейтинг должен быть от 1 до 5.

### Uvicorn

Uvicorn запускает FastAPI-приложение:

```bash
uvicorn main:app --reload
```

## 3. Структура проекта

```text
exam_week1/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── crud.py
├── sqlite_database.py
├── requirements.txt
└── frontend/
```

Главные рабочие файлы:

- `database.py` — подключение к базе данных;
- `models.py` — таблицы базы данных;
- `schemas.py` — проверка входящих и исходящих данных;
- `crud.py` — запросы к базе и бизнес-логика;
- `main.py` — адреса API, которые вызывает пользователь.

Общий путь запроса:

```text
Клиент -> main.py -> schemas.py -> crud.py -> models.py -> SQLite
```

## 4. Объяснение database.py

### Адрес базы данных

```python
DATABASE_URL = "sqlite:///./internet_shop.db"
```

Это означает: использовать SQLite и создать файл `internet_shop.db` в папке проекта.

### Engine

```python
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
```

`engine` отвечает за соединение SQLAlchemy с базой данных.

`check_same_thread=False` нужен для работы SQLite с запросами FastAPI.

### SessionLocal

```python
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
```

Сессия используется для выполнения запросов к базе. Через неё вызываются `query`, `add`, `delete`, `commit` и другие методы.

### Base

```python
class Base(DeclarativeBase):
    pass
```

Все модели наследуются от `Base`. Благодаря этому SQLAlchemy понимает, что классы из `models.py` являются таблицами.

### get_db

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Функция создаёт сессию для одного HTTP-запроса, передаёт её endpoint и обязательно закрывает после завершения.

Что можно сказать учителю:

> Я использовал dependency `get_db`, чтобы каждый запрос получал отдельную сессию базы данных и после работы сессия закрывалась.

## 5. Объяснение models.py

`models.py` описывает таблицы и связи между ними.

### Основные конструкции SQLAlchemy

```python
id: Mapped[int] = mapped_column(primary_key=True)
```

- `Mapped[int]` — тип поля;
- `mapped_column` — колонка таблицы;
- `primary_key=True` — первичный ключ;
- `nullable=False` — значение обязательно;
- `unique=True` — значение не должно повторяться;
- `ForeignKey` — внешний ключ, который связывает таблицы;
- `relationship` — ORM-связь между Python-объектами.

### User

Таблица `users` хранит:

- `id` — идентификатор пользователя;
- `name` — имя;
- `email` — уникальный email.

У пользователя есть корзина, заказы, отзывы и избранные товары.

### Category

Таблица `categories` хранит категории товаров.

- `id` — идентификатор;
- `name` — уникальное название;
- `products` — список товаров этой категории.

### Product

Таблица `products` хранит:

- название;
- описание;
- цену;
- количество на складе;
- `category_id`.

Связь с категорией:

```python
category_id = mapped_column(ForeignKey("categories.id"))
category = relationship(back_populates="products")
```

Один товар относится к одной категории, а одна категория может содержать много товаров.

### CartItem

Каждая строка `cart_items` — один вид товара в корзине пользователя.

```python
UniqueConstraint("user_id", "product_id")
```

Это запрещает хранить одинаковый товар два раза для одного пользователя. Если товар уже существует в корзине, код увеличивает `quantity`.

### Order и OrderItem

`Order` хранит общую информацию о заказе:

- пользователь;
- общая сумма;
- статус;
- дата создания.

`OrderItem` хранит товары конкретного заказа:

- `order_id`;
- `product_id`;
- название товара;
- цену во время покупки;
- количество;
- subtotal.

Цена сохраняется в `OrderItem`, потому что цена товара может измениться после оформления заказа. История должна показывать старую цену покупки.

### Review

Таблица отзывов хранит пользователя, товар, рейтинг и комментарий.

Рейтинг проверяется в `schemas.py` и может быть только от 1 до 5.

### Favorite

Таблица избранных товаров связывает пользователя и товар.

```python
UniqueConstraint("user_id", "product_id")
```

Один пользователь не может два раза добавить один товар в избранное.

### Cascade

```python
relationship(cascade="all, delete-orphan")
```

Это означает, что связанные дочерние данные могут удаляться вместе с родительским объектом.

## 6. Объяснение schemas.py

Модели SQLAlchemy описывают базу данных, а Pydantic-схемы описывают данные API.

### Зачем нужны Create, Update и Read

Например:

- `ProductCreate` — что клиент отправляет для создания товара;
- `ProductUpdate` — что отправляется для обновления;
- `ProductRead` — что API возвращает;
- `ProductNested` — товар вместе с вложенной категорией.

### Проверка пустого текста

```python
def clean_text(value: str):
    if not value.strip():
        raise ValueError("Field cannot be empty")
    return value.strip()
```

`strip()` удаляет пробелы по краям. Строка из одних пробелов не принимается.

### Field

```python
price: float = Field(gt=0)
stock: int = Field(ge=0)
rating: int = Field(ge=1, le=5)
```

- `gt=0` — строго больше нуля;
- `ge=0` — больше или равно нулю;
- `le=5` — меньше или равно пяти.

### Literal

```python
status: Literal["new", "paid", "cancelled"]
```

Можно передать только один из трёх разрешённых статусов.

### from_attributes

```python
model_config = ConfigDict(from_attributes=True)
```

Это позволяет Pydantic читать данные из объектов SQLAlchemy.

### Nested response

```python
class OrderRead(BaseModel):
    ...
    items: list[OrderItemRead]
```

Когда API возвращает заказ, внутри него сразу возвращается список товаров заказа.

## 7. Объяснение crud.py

CRUD означает:

- Create — создать;
- Read — получить;
- Update — обновить;
- Delete — удалить.

В `crud.py` модели импортируются прямо:

```python
from models import CartItem, Category, Favorite, Order, OrderItem, Product, Review, User
```

Так функции выглядят просто:

```python
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
```

### Основные команды SQLAlchemy

```python
db.query(User)
```

Начинает запрос к таблице пользователей.

```python
.filter(User.id == user_id)
```

Добавляет условие WHERE.

```python
.first()
```

Возвращает первый объект или `None`.

```python
.all()
```

Возвращает список всех найденных объектов.

```python
db.add(new_user)
db.commit()
db.refresh(new_user)
```

- `add` добавляет объект в сессию;
- `commit` сохраняет изменения;
- `refresh` получает из базы актуальные поля, например новый `id`.

### Пользователи

`get_users` возвращает пользователей по `id`.

`get_user` ищет одного пользователя.

`create_user` проверяет повтор email, создаёт `new_user` и сохраняет его.

`update_user` получает уже найденный объект `db_user`, меняет имя и email.

`delete_user` принимает объект пользователя и удаляет его.

Такой стиль разделяет обязанности: `main.py` проверяет, найден ли объект, а CRUD работает с готовым объектом.

### Категории

`get_categories` умеет искать и сортировать категории.

```python
Category.name.ilike(f"%{search}%")
```

`ilike` выполняет поиск без учёта регистра. Знаки `%` означают, что текст может находиться в любой части названия.

Категорию с товарами удалять нельзя.

### Товары

`get_products` выполняет:

- поиск по названию;
- фильтр по категории;
- минимальную и максимальную цену;
- фильтр наличия;
- сортировку;
- pagination.

Безопасная сортировка:

```python
columns = {
    "id": Product.id,
    "name": Product.name,
    "price": Product.price,
    "stock": Product.stock,
}
column = columns.get(sort_by, Product.id)
```

Пользователь не передаёт SQL-колонку напрямую. Он выбирает только разрешённое значение из словаря.

Pagination:

```python
query.offset(skip).limit(limit).all()
```

- `offset` пропускает записи;
- `limit` ограничивает количество результатов.

Товар нельзя создать без существующей категории. Товар нельзя удалить, если он находится в активном заказе.

### Корзина

`get_cart_item` получает одну строку корзины.

`get_cart_items` получает всю корзину пользователя вместе с товарами.

При добавлении товара выполняются проверки:

1. пользователь существует;
2. товар существует;
3. stock не равен нулю;
4. количество после добавления не больше stock.

Если товар уже в корзине:

```python
item.quantity = new_quantity
```

Если товара ещё нет:

```python
item = CartItem(**data.model_dump())
db.add(item)
```

Subtotal одного товара:

```python
subtotal = item.product.price * item.quantity
```

Общая сумма корзины — сумма всех subtotal.

### Создание заказа

Сложная логика разделена на маленькие функции.

`get_order_total` проверяет stock и считает общую сумму.

`add_order_items`:

- создаёт строки `OrderItem`;
- сохраняет цену покупки;
- уменьшает stock;
- удаляет товары из корзины.

`create_order` выполняет шаги:

1. проверяет пользователя;
2. получает корзину;
3. запрещает пустую корзину;
4. считает сумму;
5. создаёт заказ;
6. вызывает `db.flush()`, чтобы получить `order.id` до commit;
7. добавляет товары заказа;
8. делает commit.

```python
try:
    ...
    db.commit()
except Exception:
    db.rollback()
    raise
```

Если при создании заказа происходит ошибка, `rollback` отменяет незавершённые изменения.

### Отмена заказа

При статусе `cancelled` код проходит по товарам заказа и возвращает количество на склад:

```python
product.stock += item.quantity
```

Повторно изменить уже отменённый заказ нельзя.

### История покупок

Отменённые заказы не учитываются в сумме покупок и статистике.

Используются:

- `func.sum` — сумма;
- `group_by` — группировка по товару;
- `order_by` — сортировка.

### Отзывы

Перед созданием отзыва проверяются пользователь и товар.

Средний рейтинг считается через:

```python
func.avg(Review.rating)
```

Для поиска товаров по среднему рейтингу используется `having`, потому что условие применяется после `group_by`.

### Избранное

`get_favorite` проверяет пару `user_id + product_id`.

Если такая запись уже существует, API возвращает ошибку и не создаёт дубликат.

### Статистика

`shop_statistics` возвращает:

- количество пользователей;
- количество товаров;
- количество категорий;
- количество заказов;
- общую сумму заказов;
- среднюю сумму заказа.

`best_selling_product` группирует проданные товары и сортирует их по общему quantity.

`top_user` группирует заказы по пользователям и находит пользователя с максимальной суммой покупок.

## 8. Объяснение main.py

`main.py` связывает HTTP-запросы с функциями CRUD.

### Создание приложения

```python
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Internet Shop API", version="1.0.0")
```

`create_all` создаёт отсутствующие таблицы. `app` — объект FastAPI.

### Depends

```python
db: Session = Depends(get_db)
```

FastAPI вызывает `get_db` и передаёт открытую сессию в endpoint.

### response_model

```python
@app.post("/users/", response_model=schemas.UserRead)
```

`response_model` указывает формат ответа и скрывает лишние поля.

### Query

```python
page: int = Query(1, ge=1)
page_size: int = Query(10, ge=1, le=100)
```

FastAPI проверяет query-параметры. Номер страницы начинается с 1, размер страницы — от 1 до 100.

### HTTPException

```python
raise HTTPException(status_code=404, detail="Product not found")
```

- 404 — объект не найден;
- 400 — запрос логически неправильный;
- 422 — данные не прошли Pydantic validation;
- 201 — объект успешно создан.

### HTTP-методы

- `GET` — получить данные;
- `POST` — создать;
- `PUT` — полностью обновить;
- `PATCH` — изменить часть данных или выполнить действие;
- `DELETE` — удалить.

### Главные endpoints

Пользователи:

```text
POST   /users/
GET    /users/
GET    /users/{user_id}
PUT    /users/{user_id}
DELETE /users/{user_id}
```

Категории:

```text
POST   /categories/
GET    /categories/
GET    /categories/{category_id}
PUT    /categories/{category_id}
DELETE /categories/{category_id}
GET    /categories/{category_id}/products/
```

Товары:

```text
POST   /products/
GET    /products/
GET    /products/{product_id}
PUT    /products/{product_id}
DELETE /products/{product_id}
GET    /products/cheap/
GET    /products/expensive/
GET    /products/out-of-stock/
GET    /products/low-stock/
GET    /products/{product_id}/similar/
```

Корзина:

```text
POST   /cart/add/
GET    /cart/{user_id}
PUT    /cart/items/{cart_item_id}
PATCH  /cart/items/{cart_item_id}/decrease
DELETE /cart/items/{cart_item_id}
DELETE /cart/clear/{user_id}
```

Заказы:

```text
POST  /orders/create/
GET   /orders/
GET   /orders/{order_id}
PATCH /orders/{order_id}/status
PATCH /orders/{order_id}/cancel
```

Отзывы и избранное:

```text
POST   /products/{product_id}/reviews/
GET    /products/{product_id}/reviews/
GET    /products/{product_id}/rating/
DELETE /reviews/{review_id}
POST   /favorites/
GET    /favorites/{user_id}
GET    /favorites/{user_id}/{product_id}/check
DELETE /favorites/{user_id}/{product_id}
```

## 9. Примеры запросов

### Создание категории

```json
{
  "name": "Phones"
}
```

### Создание товара

```json
{
  "name": "iPhone",
  "description": "Smartphone",
  "price": 1000,
  "stock": 10,
  "category_id": 1
}
```

### Поиск и фильтрация

```text
GET /products/?search=phone&category_id=1&min_price=100&max_price=1500
```

### Сортировка и pagination

```text
GET /products/?sort_by=price&order=desc&page=2&page_size=5
```

Формула pagination:

```python
skip = (page - 1) * page_size
```

### Добавление в корзину

```json
{
  "user_id": 1,
  "product_id": 1,
  "quantity": 2
}
```

### Создание заказа

```json
{
  "user_id": 1
}
```

### Добавление отзыва

```json
{
  "user_id": 1,
  "rating": 5,
  "comment": "Very good product"
}
```

## 10. Как запустить проект

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger открывается по адресу:

```text
http://127.0.0.1:8000/docs
```

Swagger позволяет запускать endpoints без отдельного frontend.

## 11. Частые вопросы учителя

### Почему отдельно models и schemas?

`models.py` описывает таблицы базы. `schemas.py` проверяет данные API и задаёт формат ответа.

### Зачем нужен crud.py?

Чтобы запросы к базе и бизнес-логика не находились внутри endpoints. Так код проще читать и поддерживать.

### Что такое relationship?

Это связь между ORM-объектами. Например, через `category.products` можно получить товары категории.

### Что такое ForeignKey?

Внешний ключ связывает строки разных таблиц. Например, `Product.category_id` указывает на `Category.id`.

### Зачем commit и refresh?

`commit` сохраняет изменения. `refresh` обновляет объект из базы и получает созданный `id`.

### Зачем flush при заказе?

`flush` отправляет новый заказ в базу внутри текущей транзакции, чтобы получить его `id`, но ещё не завершает всю транзакцию.

### Почему цена хранится в OrderItem?

Чтобы история заказа не менялась, если позже изменить текущую цену товара.

### Как запрещается заказать больше stock?

Перед созданием заказа `get_order_total` сравнивает `item.quantity` и `item.product.stock`.

### Как работает отмена?

Статус меняется на `cancelled`, а quantity каждого товара прибавляется обратно к stock.

### Чем filter отличается от having?

`filter` применяется к обычным строкам до группировки. `having` применяется к результатам `group_by`, например к среднему рейтингу.

### Что такое nested response?

Это ответ с вложенными данными. Например, заказ возвращается сразу со списком `items`, а товар — с категорией.

## 12. Короткая речь для защиты

> Я сделал backend интернет-магазина на FastAPI, SQLAlchemy и SQLite. Проект разделён на database, models, schemas, crud и main. Models описывают таблицы и relationships, schemas выполняют validation, CRUD работает с базой, а main содержит endpoints. В товарах есть поиск, фильтры, сортировка и pagination. Корзина проверяет наличие и stock, одинаковый товар увеличивает quantity. При создании заказа сохраняется текущая цена, уменьшается stock и очищается корзина. При отмене stock возвращается. Также реализованы история покупок, статистика, отзывы, рейтинг и избранное. Ошибки возвращаются через HTTPException, а документация доступна в Swagger.

## 13. Самое главное, что нужно запомнить

1. `main.py` принимает HTTP-запрос.
2. `schemas.py` проверяет данные.
3. `crud.py` выполняет логику и запросы.
4. `models.py` описывает таблицы.
5. `database.py` создаёт сессию SQLite.
6. `commit` сохраняет, `refresh` обновляет объект.
7. `ForeignKey` и `relationship` связывают таблицы.
8. Корзина проверяет stock.
9. Заказ сохраняет цену покупки и уменьшает stock.
10. Swagger показывает и запускает все endpoints.
