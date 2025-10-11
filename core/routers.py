from rest_framework import routers
from room.views import HouseViewSet, RoomViewSet, TenantViewSet, PaymentHistoryViewSet, TenantDocumentViewSet, PaymentReceivedViewSet

router = routers.DefaultRouter()

router.register('houses', HouseViewSet, basename='house')
router.register('rooms', RoomViewSet, basename='room')
router.register('tenants', TenantViewSet, basename='tenant')
router.register('payment-histories', PaymentHistoryViewSet, basename='paymenthistory')
router.register('tenant-documents', TenantDocumentViewSet, basename='tenantdocument')
router.register('payment-received', PaymentReceivedViewSet, basename='paymentreceived')