from rest_framework import routers
from room.views import HouseViewSet, RoomViewSet, TenantViewSet, PaymentHistoryViewSet

router = routers.DefaultRouter()

router.register('houses', HouseViewSet, basename='house')
router.register('rooms', RoomViewSet, basename='room')
router.register('tenants', TenantViewSet, basename='tenant')
router.register('payment-histories', PaymentHistoryViewSet, basename='paymenthistory')