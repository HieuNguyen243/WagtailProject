# crm/signals.py

from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Order, OrderItem, SupportTicket


@receiver(post_save, sender=Order)
def order_saved_handler(sender, instance, **kwargs):
    """
    Khi đơn hàng chuyển sang trạng thái 'completed', tự động tính toán lại
    tổng doanh số tích lũy của khách hàng và nâng hạng thẻ thành viên.
    """
    if instance.customer and instance.status == "completed":
        instance.customer.update_tier_automatically()


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def order_item_changed_handler(sender, instance, **kwargs):
    """
    Khi thêm, sửa hoặc xóa sản phẩm trong đơn hàng, tự động cập nhật
    lại total_amount trên Order để luôn đồng nhất dữ liệu.
    """
    order = instance.order
    if order:
        items_total = sum(item.quantity * item.unit_price for item in order.items.all())
        if order.total_amount != items_total:
            Order.objects.filter(pk=order.pk).update(total_amount=items_total)
            if order.status == "completed" and order.customer:
                order.customer.update_tier_automatically()


@receiver(post_save, sender=SupportTicket)
def support_ticket_saved_handler(sender, instance, **kwargs):
    """
    Khi ticket được đánh dấu là 'resolved' hoặc 'closed', tự động
    cập nhật thời gian giải quyết resolved_at.
    """
    if instance.status in ["resolved", "closed"] and not instance.resolved_at:
        SupportTicket.objects.filter(pk=instance.pk).update(resolved_at=timezone.now())
