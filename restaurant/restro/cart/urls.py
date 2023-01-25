from django.urls import path
from cart.views import *


urlpatterns = [

    
    path('addcart',AddProductCart.as_view(), name='addcart'),
    path('viewcart',ViewCartProduct.as_view(), name='viewcart'),
    path('deletecart/<int:id>',DeleteCartItem.as_view(), name='deletecart'),
    path('deletecartbyid/<int:id>',DeleteCartItemById.as_view(), name='deletecartbyid'),
    
]