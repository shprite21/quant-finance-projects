import json
from datamodel import Order

class Trader:

    LIMITS = {
        "ASH_COATED_OSMIUM": 80,
        "INTARIAN_PEPPER_ROOT": 80
    }

    def bid(self):
        return 22

    def run(self, state):
        result = {}
        data = json.loads(state.traderData) if state.traderData else {}

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

            
            # ASH_COATED_OSMIUM
            
            if product == "ASH_COATED_OSMIUM":

                fair = 10000 - 0.30 * pos

                # Dynamic spread based on deviation from anchor
                vol = abs(mid - 10000)
                spread = 1 if vol < 2 else 2

                bid_px = min(best_bid + 1, int(fair - spread / 2))
                ask_px = max(best_ask - 1, int(fair + spread / 2))

                buy_qty = LIMIT - pos
                sell_qty = LIMIT + pos

                if buy_qty > 0:
                    orders.append(Order(product, bid_px, buy_qty))

                if sell_qty > 0:
                    orders.append(Order(product, ask_px, -sell_qty))

            
            # INTARIAN_PEPPER_ROOT
            
            else:

                # infer base trend once
                if product not in data:
                    data[product] = mid - 0.01 * state.timestamp

                base = data[product]

                fair = base + 0.01 * state.timestamp

                # nonlinear inventory skew
                fair -= 0.15 * pos + 0.002 * pos * abs(pos)

                # book imbalance alpha
                bid_vol = sum(od.buy_orders.values())
                ask_vol = -sum(od.sell_orders.values())

                imb = (bid_vol - ask_vol) / (bid_vol + ask_vol + 1e-6)

                fair += 0.25 * imb

                
                # Dynamic spread + edge
                
                vol = abs(mid - fair)

                spread = 2 if vol < 2 else 3
                edge = 1 if vol > 1 else 2

                bid_px = min(best_bid + 1, int(fair - spread / 2))
                ask_px = max(best_ask - 1, int(fair + spread / 2))

                buy_qty = LIMIT - pos
                sell_qty = LIMIT + pos

                # Aggressive taking
                if best_ask <= fair - edge:
                    qty = min(-od.sell_orders[best_ask], buy_qty)
                    if qty > 0:
                        orders.append(Order(product, best_ask, qty))
                        buy_qty -= qty

                if best_bid >= fair + edge:
                    qty = min(od.buy_orders[best_bid], sell_qty)
                    if qty > 0:
                        orders.append(Order(product, best_bid, -qty))
                        sell_qty -= qty

                # Passive quoting
                if buy_qty > 0:
                    orders.append(Order(product, bid_px, buy_qty))

                if sell_qty > 0:
                    orders.append(Order(product, ask_px, -sell_qty))

            result[product] = orders

        return result, 0, json.dumps(data)