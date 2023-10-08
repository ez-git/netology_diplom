from django.urls import path, include
from rest_framework import routers
from orders.views import (
    RegisterAccount,
    LoginAccount,
    PartnerUpdate,
    ShopView,
    CategoryView,
    ProductInfoView,
    BasketView,
    OrderView,
    ConfirmAccount,
    OrderConfirmView
)

app_name = 'orders'

router = routers.SimpleRouter()
router.register(r'shops', ShopView)
router.register(r'categories', CategoryView)
router.register(r'products', ProductInfoView, basename='products')

urlpatterns = [
    path('user/register/', RegisterAccount.as_view()),
    path('user/confirm/', ConfirmAccount.as_view()),
    path('user/login/', LoginAccount.as_view()),
    path('partner/update/', PartnerUpdate.as_view()),
    path('basket/', BasketView.as_view()),
    path('order/', OrderView.as_view()),
    path('order/confirm/', OrderConfirmView.as_view()),
    path('', include(router.urls))
]

urlpatterns += router.urls
