// APIMatic-context-grounded SDK 2.5.0 example. Builds arguments only; no API/client/network call.
import { CheckoutPaymentIntent } from '@paypal/paypal-server-sdk';
import type { OrdersController, PaymentsController } from '@paypal/paypal-server-sdk';

export type CreateArgs = Parameters<OrdersController['createOrder']>[0];
export type CaptureArgs = Parameters<OrdersController['captureOrder']>[0];
export type RefundArgs = Parameters<PaymentsController['refundCapturedPayment']>[0];

function identifier(value: string): string {
  if (!value || value.length > 100 || /[\x00-\x20\x7f]/.test(value)) throw new Error('invalid_identity');
  return value;
}

export function createUSDOrder(amount: string, stableRequestId: string): CreateArgs {
  if (!/^(0|[1-9][0-9]{0,6})\.[0-9]{2}$/.test(amount) || amount === '0.00') throw new Error('invalid_usd_amount');
  return { paypalRequestId: identifier(stableRequestId), body: {
    intent: CheckoutPaymentIntent.Capture,
    purchaseUnits: [{ amount: { currencyCode: 'USD', value: amount } }],
  } };
}

export function captureExistingOrder(orderId: string, sameOperationRequestId: string): CaptureArgs {
  return { id: identifier(orderId), paypalRequestId: identifier(sameOperationRequestId) };
}

export function refundOriginalV2Capture(captureId: string, refundRequestId: string): RefundArgs {
  // Caller must establish V2 capture/account/environment origin; never supply an NVP transaction ID.
  return { captureId: identifier(captureId), paypalRequestId: identifier(refundRequestId) };
}
