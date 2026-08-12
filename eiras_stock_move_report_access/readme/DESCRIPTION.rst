By default, Odoo only shows the Inventory > Reporting > Moves menu
(``stock.stock_move_menu``) when the browser session has developer mode
active — this is hardcoded in Odoo core (``ir.ui.menu._visible_menu_ids``),
regardless of the security groups actually assigned to the user.

This module replaces that menu's technical group requirement with the
regular Inventory user group, so any user with Inventory access — including
the fuel/diesel refueling data added by the ``fuel_stock_consume`` modules,
which extend this same list — can reach it without needing developer mode.
