# Data Schema

Columns in `listings_generated.xlsx` and `listings.parquet`:
- `id` (str): unique listing id.
- `city` (str): city name.
- `district` (str): district/area within city.
- `price` (float): listing price in local currency units.
- `bedrooms` (int): number of bedrooms.
- `bathrooms` (int): number of bathrooms.
- `area_sqm` (float): usable area in square meters.
- `property_type` (str): e.g., apartment, house.
- `year_built` (int): construction year.
- `has_parking` (bool): parking availability.
- `description` (str): short unstructured blurb.
- `listing_date` (date): simulated posting date.

Distribution notes (expected ranges)
- price: 0.5M - 10M with right skew.
- bedrooms: 1 - 5.
- bathrooms: 1 - 4.
- area_sqm: 35 - 300.
- year_built: 1970 - current year.
