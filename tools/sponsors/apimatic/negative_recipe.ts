// Deliberate compiler negatives: three independent fabricated SDK assumptions must fail.
import type { OrdersController, PaymentsController } from '@paypal/paypal-server-sdk';
type WrongMethod = OrdersController['ordersCreate'];
const wrongCapture: Parameters<OrdersController['captureOrder']>[0] = { captureId: 'SYNTHETIC' };
const wrongRefund: Parameters<PaymentsController['refundCapturedPayment']>[0] = { id: 'SYNTHETIC' };
export { wrongCapture, wrongRefund };
export type { WrongMethod };
