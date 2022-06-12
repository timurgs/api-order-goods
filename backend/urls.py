from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from backend.views import PartnerUpdate, ProductInfoView, RegisterView, LoginView, ConfirmView, \
    BasketView, ResetPasswordRequestTokenView, ResetPasswordView, OrderConfirmView, ContactsView, OrdersViewSet, \
    PartnerState, PartnerOrders, AccountData, CategoryView, ShopView

app_name = 'backend'

router = DefaultRouter()
router.register(r'orders', OrdersViewSet, basename='orders')

urlpatterns = [
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
    path('products', ProductInfoView.as_view(), name='products'),
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('accountconfirm', ConfirmView.as_view(), name='confirm'),
    path('basket', BasketView.as_view(), name='basket'),
    path('resetpasswordtoken', ResetPasswordRequestTokenView.as_view(), name='reset-password-token'),
    path('resetpassword', ResetPasswordView.as_view(), name='reset-password'),
    path('orderconfirm', OrderConfirmView.as_view(), name='order-confirm'),
    path('contacts', ContactsView.as_view(), name='contacts'),
    path('account/data', AccountData.as_view(), name='account-data'),
    path('category', CategoryView.as_view(), name='category'),
    path('shop', ShopView.as_view(), name='shop'),
    path('', include(router.urls)),
    path('schema', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui', SpectacularSwaggerView.as_view(url_name='backend:schema'), name='swagger-ui'),
    path('schema/redoc', SpectacularRedocView.as_view(url_name='backend:schema'), name='redoc'),
]
