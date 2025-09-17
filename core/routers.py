from rest_framework import routers
from room.views import RoomViewSet, TenantViewSet, PaymentHistoryViewSet

router = routers.DefaultRouter()

router.register('rooms', RoomViewSet, basename='room')
router.register('tenants', TenantViewSet, basename='tenant')
router.register('payment-histories', PaymentHistoryViewSet, basename='paymenthistory')