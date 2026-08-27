# -*- coding: utf-8 -*-
from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    choosing_quantity = State()
    entering_name = State()
    entering_phone = State()
    entering_address = State()
    choosing_payment = State()
    waiting_receipt = State()


class AdminStates(StatesGroup):
    add_product_category = State()
    add_product_size = State()
    add_product_price = State()
    add_product_unit = State()
    set_image_category = State()
    set_image_waiting_photo = State()
