from datetime import datetime

from typing import Optional

from pytune_data.models import Manufacturer, ManufacturerSerialNumber
from pytune_data.db import init
from tortoise.exceptions import DoesNotExist
import re
from simple_logger.logger import get_logger, SimpleLogger

logger : SimpleLogger = get_logger()

async def get_manufacturer_name(manufacturer_id: int) -> Optional[str]:
    """Récupère le nom du fabricant à partir de son ID."""
    await init()
    try:
        manufacturer = await Manufacturer.get(id=manufacturer_id)
        return manufacturer.company
    except DoesNotExist:
        return None

async def get_serial_number_info(manufacturer_id: int, serial_number: str, max_extrapolation_years: int = 15):
    """
    Finds the manufacturing year of a piano based on its serial number.
    
    Process:
    1️⃣ If the serial number is **lower** than the first known, returns: **"Probably earlier than XXXX"**.
    2️⃣ If the serial number **exists in the database**, returns the exact year.
    3️⃣ If the serial number is **higher** than the last known, it **extrapolates**:
        - Uses the last known growth rate.
        - Limits extrapolation to **max_extrapolation_years** (default: 15 years).
        - Ensures the estimated year **does not exceed the current year + 5** (safety check).
    4️⃣ If no exact match but falls within a known range, returns the closest **previous year**.
    
    Parameters:
    - `manufacturer_id` (int): The ID of the manufacturer.
    - `serial_number` (str): The serial number to look up.
    - `max_extrapolation_years` (int): The maximum years allowed for extrapolation beyond known data.

    Returns:
    - A dictionary: {"year": str/int, "manufacturer": str, "confidence": int}
    """
    await init()

    # ✅ Clean the serial number: remove letters & leading zeros
    serial_number_int = ''.join(filter(str.isdigit, serial_number)).lstrip("0")
    serial_number_int = int(serial_number_int) if serial_number_int.isdigit() else None

    if not serial_number_int:
        return None  # 🚨 Unusable serial number

    # 🔍 Get the first and last known serial number entries
    first_entry = await ManufacturerSerialNumber.filter(
        manufacturer_id=manufacturer_id
    ).order_by("serial_number_int").first()

    last_entry = await ManufacturerSerialNumber.filter(
        manufacturer_id=manufacturer_id
    ).order_by("-serial_number_int").first()

    # Ensure valid data exists
    if not first_entry or not last_entry:
        return None  # 🚨 No data available for this manufacturer

    # 1️⃣ **Serial number is older than the first known**
    if serial_number_int < first_entry.serial_number_int:
        return {
            "year": f"Probably earlier than {first_entry.year}",
            "manufacturer": await get_manufacturer_name(manufacturer_id),
            "confidence": 50  # Lower confidence for very old numbers
        }

    # 2️⃣ **Serial number is newer than the last known → Extrapolation**
    if serial_number_int > last_entry.serial_number_int:
        last_five_entries = await ManufacturerSerialNumber.filter(
            manufacturer_id=manufacturer_id
        ).order_by("-year").limit(5)

        if len(last_five_entries) > 1:
            total_growth = last_five_entries[0].serial_number_int - last_five_entries[-1].serial_number_int
            total_years = last_five_entries[0].year - last_five_entries[-1].year

            avg_growth_per_year = total_growth / total_years if total_years > 0 else 0

            if avg_growth_per_year > 0:  # Ensure valid growth rate
                estimated_years_ahead = (serial_number_int - last_entry.serial_number_int) / avg_growth_per_year
                estimated_year = last_entry.year + round(estimated_years_ahead)

                # 🔹 Set extrapolation limit dynamically
                current_year = datetime.now().year
                max_extrapolation_year = min(current_year + 5, last_entry.year + max_extrapolation_years)

                estimated_year = min(estimated_year, max_extrapolation_year)

                # 🔹 Calculate confidence: Decreases as we extrapolate further
                confidence = max(60, 100 - (estimated_year - last_entry.year) * 3)

                return {
                    "year": f"Estimated extrapolation: {estimated_year}",
                    "manufacturer": await get_manufacturer_name(manufacturer_id),
                    "confidence": confidence
                }

        # 🔹 Unable to extrapolate → Provide general estimate
        return {
            "year": f"Probably later than {last_entry.year}",
            "manufacturer": await get_manufacturer_name(manufacturer_id),
            "confidence": 50  # Low confidence due to lack of recent data
        }

    # 3️⃣ **Find the closest known range**
    closest_entry = await ManufacturerSerialNumber.filter(
        manufacturer_id=manufacturer_id,
        serial_number_int__lte=serial_number_int
    ).order_by("-serial_number_int").first()

    if closest_entry:
        return {
            "year": closest_entry.year,
            "manufacturer": await get_manufacturer_name(manufacturer_id),
            "confidence": 100  # High confidence when found in the database
        }

    return None  # 🚨 Unlikely scenario

async def get_serial_year(manufacturer_id: int, serial_number: str) -> Optional[int]:
    """
    Trouve l'année approximative d'un piano en fonction de son numéro de série.
    Si le numéro dépasse le dernier connu, on extrapole.
    """
    await init()

    cleaned_serial = re.sub(r'^[A-Za-z]+', '', serial_number).lstrip('0')

    try:
        serial_int = int(cleaned_serial)
    except ValueError:
        return None  # 🚨 Numéro invalide

    # 🔍 Recherche de la tranche la plus proche
    closest_entry = await ManufacturerSerialNumber.filter(
        manufacturer_id=manufacturer_id,
        serial_number_int__lte=serial_int
    ).order_by('-serial_number_int').first()

    if closest_entry:
        return closest_entry.year

    return None  # 🚨 Rien trouvé
