import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from catalogue_service import check_catalogue_membership, CatalogueStatus, resolve_coordinates_from_catalogue

tests = [
    ('Ajanta Caves (Cave 19)', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('Ajanta Caves', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('ajanta_caves', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('Eiffel Tower', CatalogueStatus.OUT_OF_CATALOG),
    ('Tour Eiffel', CatalogueStatus.OUT_OF_CATALOG),
    ('Golden Temple', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('Harmandir Sahib', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('Mysore Palace', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('Amba Vilas Palace', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('Taj Mahal', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('Crown of the Palace', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('Qutub Minar', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('Qutb Minar', CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY),
    ('Generic Random Castle', CatalogueStatus.OUT_OF_CATALOG),
    ('Receipt Invoice Document', CatalogueStatus.OUT_OF_CATALOG)
]

print("=== EXECUTING CATALOGUE MEMBERSHIP TEST CASES ===")
all_passed = True
for name, expected in tests:
    res = check_catalogue_membership(name)
    ok = res.status == expected
    if not ok:
        all_passed = False
    status_str = "PASS" if ok else "FAIL"
    print(f"[{status_str}] \"{name}\" -> {res.status.value} (ID: {res.monument_id}, Match: {res.match_method}) [Expected: {expected.value}]")

# Test coordinate resolution
coords, cid, src = resolve_coordinates_from_catalogue("Ajanta Caves (Cave 19)")
print(f"\nAjanta Caves coordinate resolution: coords={coords}, id={cid}, src={src}")
assert coords is not None and coords.get("lat") is not None, "Ajanta Caves coordinates must resolve!"

coords_eiffel, cid_eiffel, _ = resolve_coordinates_from_catalogue("Eiffel Tower")
print(f"Eiffel Tower coordinate resolution: coords={coords_eiffel}, id={cid_eiffel} (Must be None)")
assert coords_eiffel is None, "Eiffel Tower must not resolve coordinates since it is OUT_OF_CATALOG!"

if all_passed:
    print("\nALL CATALOGUE MEMBERSHIP TESTS PASSED SUCCESSFULLY!")
else:
    sys.exit(1)

