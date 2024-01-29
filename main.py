from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from .model.core import CourierTable, DistrictTable, OrderTable, Base
from .model.schema import CreateCourierModel, CourierResponseModel, CoruierDetailResponseModel, CreateOrderModel, OrderResponseModel

engine = create_engine("sqlite:///database1.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False,bind=engine)
session = SessionLocal()
Base.metadata.create_all(bind=engine)

app = FastAPI()


#пустышка
@app.get('/')
async def start_page():
    return 'Hello'

#эндпоинт не принимает ничего, выводит список курьеров с полями: id:int , имя: str
@app.get('/courier')
async def see_couriers():
    couriers = session.query(CourierTable).all()
    return [CourierResponseModel(id=courier.id,name=courier.name) for courier in couriers]


#принимает query с полями имя: str, районы: list[str]. Список районов сделан через отдельную таблицу, которая привязана к таблице курьеров. 
@app.post('/courier')
async def create_courier(courier: CreateCourierModel):
    new_courier = CourierTable(name = courier.name)
    for district in courier.district:
        new_district = DistrictTable(name=district)
        new_courier.districts.append(new_district)
    session.add(new_courier)
    session.commit()
    session.refresh(new_courier)
    return {'message' : 'курьер добавлен!'}

#Принимает id курьера - возвращает "карточку курьера": id: int, имя, активный заказ( dict{id заказа})  - ecли у курьера нет активног заказа и он "не занят"(isBusy == False), active_order = null  
#среднее время выполнения заказа(по дефолту null, чтобы не было каши), среднее количество выполненных заказов в день. Если курьер не найден, поднимаем ошибку с кодом 404
@app.get('/courier/{courier_id}')
async def get_courier(courier_id: int):
    courier = session.query(CourierTable).get(courier_id)
    if not courier.isBusy and courier.active_order:
        courier.active_order = None
        session.commit()
    if not courier:
        raise HTTPException(status_code=404, detail='Курьер не найден')
    active_order = None
    if courier.active_order:
        active_order = {'order.id': courier.active_order.id, 'order_name': courier.active_order.name}
        
    return CoruierDetailResponseModel(
        id= courier.id,
        name= courier.name,
        active_order= active_order,
        avg_order_complete_time= courier.avg_order_complete_time,
        avg_order_day= courier.avg_order_day
    )

#принимает имя и район заказа, делает запрос в бд с фильтрами: подходящий район, курьер не занят. Если курьер не найден, возвращаем ошибку 404. Дальше добавляем запись в таблицу заказов
#меняем поле isBusy у курьера на True(с ним проще искать свободных курьеров).
@app.post('/order')
async def create_order(order: CreateOrderModel):
    courier = session.query(CourierTable).join(DistrictTable).filter(DistrictTable.name == order.district).filter(CourierTable.isBusy == False).first()
    if not courier:
        raise HTTPException(status_code=404, detail='Не найден подходящий курьер')
    new_order = OrderTable(name=order.name, district=order.district, courier=courier)
    try:
        session.add(new_order)
        courier.isBusy = True
        session.commit()
        session.refresh(new_order)
        return {'order_id': new_order.id, 'courier_id': courier.id}
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
#Принимает id заказа, делает запрос в таблицу по id. Если заказа с таким id в таблицен нет, возвращает ошибку 404, иначе возвращает id курьера, за которым закреплён заказ и статус заказа 1 - в работе, 2 - завершён
@app.get('/order/{order_id}')
async def get_order(order_id: int):
    order = session.query(OrderTable).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail='Заказ не найден')
    return OrderResponseModel(
        courier_id= order.courier_id,
        status= order.status
    )
#принимает id заказа. Если заказ не найден, возвращает ошибку 404. Если найден: если статус 2 - возвращает ошибку 400, иначе закрывает заказ(присваивает статус 2, освобождает курьера), возвращает сообщение
#"заказ успешно завершён"
@app.post('/order/{order_id}')
async def close_order(order_id: int):
    order = session.query(OrderTable).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail='Заказ не найден')
    if order.status == 2:
        raise HTTPException(status_code=400, detail='Заказ уже был завершён')
    order.status = 2
    order.courier.isBusy = False
    try:
        session.commit()
        return {'message': 'Заказ успешно завершён'}
    except SQLAlchemyError as d:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(d))