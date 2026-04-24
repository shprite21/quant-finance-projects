import json
from datamodel import Order

class Trader:

    LIMITS = {
        "ASH_COATED_OSMIUM": 80,
        "INTARIAN_PEPPER_ROOT": 80
    }

    def bid(self):
        return 17  # smart middle bid for extra access

    def run(self, state):
        result = {}

        if state.traderData:
            data = json.loads(state.traderData)
        else:
            data = {}

        for product in state.order_depths:
            od = state.order_depths[product]
            orders = []

            if not od.buy_orders or not od.sell_orders:
                result[product] = orders
                continue

            best_bid = max(od.buy_orders.keys())
            best_ask = min(od.sell_orders.keys())
            mid = (best_bid + best_ask) / 2

            pos = state.position.get(product, 0)
            LIMIT = self.LIMITS[product]

            # =====================================
            # ASH_COATED_OSMIUM
            # =====================================
            if product == "ASH_COATED_OSMIUM":

                fair = 10000 - 0.30 * pos
                spread = 2

                bid_px = min(best_bid + 1, int(fair - 1))
                ask_px = max(best_ask - 1, int(fair + 1))

                buy_qty = LIMIT - pos
                sell_qty = LIMIT + pos

                if buy_qty > 0:
                    orders.append(Order(product, bid_px, buy_qty))

                if sell_qty > 0:
                    orders.append(Order(product, ask_px, -sell_qty))

            # =====================================
            # INTARIAN_PEPPER_ROOT
            # =====================================
            else:
                # infer base once
                if product not in data:
                    data[product] = mid - 0.01 * state.timestamp

                base = data[product]

                fair = base + 0.01 * state.timestamp
                fair -= 0.20 * pos

                spread = 3

                bid_px = min(best_bid + 1, int(fair - spread/2))
                ask_px = max(best_ask - 1, int(fair + spread/2))

                buy_qty = LIMIT - pos
                sell_qty = LIMIT + pos

                # aggressive edge
                if best_ask < fair:
                    qty = min(-od.sell_orders[best_ask], buy_qty)
                    if qty > 0:
                        orders.append(Order(product, best_ask, qty))
                        buy_qty -= qty

                if best_bid > fair:
                    qty = min(od.buy_orders[best_bid], sell_qty)
                    if qty > 0:
                        orders.append(Order(product, best_bid, -qty))
                        sell_qty -= qty

                if buy_qty > 0:
                    orders.append(Order(product, bid_px, buy_qty))

                if sell_qty > 0:
                    orders.append(Order(product, ask_px, -sell_qty))

            result[product] = orders

        return result, 0, json.dumps(data)