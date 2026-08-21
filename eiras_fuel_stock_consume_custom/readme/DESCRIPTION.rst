This module extends the Fuel Stock Consume module, adding two new
numeric fields, Initial Register Value and Final Register Value,
to the fuel consumption wizard and to the fuel consumption stock pickings
and stock moves.

In the fuel consumption wizard it also:

* fills the Source Location with the default source location of the
  selected Operation Type;
* computes the Quantity as the difference between the Initial Register Value
  and the Final Register Value (the tank level goes down when a vehicle is
  refueled), in the unit of measure of the selected product, making that
  field read-only while both readings are filled.
