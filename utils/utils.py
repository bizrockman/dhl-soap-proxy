import pycountry


def get_iso3_from_iso2(country_iso2_code):
    country = pycountry.countries.get(alpha_2=country_iso2_code)
    if country:
        return country.alpha_3
    else:
        raise ValueError("Invalid country ISO2 code.")
