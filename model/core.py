from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

Base = declarative_base()


class CourierTable(Base):
    __tablename__ = 'couriers'

    id = Column(Integer, primary_key= True, index= True, autoincrement= True)
    name = Column(String, nullable= False)
    active_order = relationship('OrderTable',uselist=False, back_populates='courier')
    districts = relationship("DistrictTable", back_populates="courier")
    avg_order_complete_time = Column(DateTime, default=None)
    avg_order_day = Column(Integer, default=10)
    isBusy = Column(Boolean, default=False)


class DistrictTable(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable= False)
    courier = relationship("CourierTable",back_populates='districts')
    coruier_id = Column(Integer, ForeignKey('couriers.id'))


class OrderTable(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key= True, index= True, autoincrement= True)
    name = Column(String, nullable=False)
    district = Column(String, nullable=False)
    courier = relationship('CourierTable', back_populates='active_order')
    courier_id = Column(Integer, ForeignKey('couriers.id'))
    status = Column(Integer, nullable= False, default=1)