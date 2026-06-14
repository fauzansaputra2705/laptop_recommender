"""Target spec profile per employee role (skripsi: PT Informatika Media Pratama).

These are the *ideal* specs a role tends to need. They are used only as a
**floor** for the cluster-routing / cosine vector so that a user's minimum
specs (which may be conservatively low) don't pull the recommendation toward a
cheaper cluster than the role actually warrants.

They do NOT affect relevance / Precision@K — that still uses the user's own
minimum specs + budget. Adjust these numbers after the PT interview
(Template_Wawancara_PT, Bagian 4 no.18).
"""

# Per role: target floor for each routing dimension.
ROLE_TARGETS = {
    "developer": {
        "processor_tier": 7,
        "ram_gb": 16,
        "storage_gb": 1024,
        "vga_type": "integrated",
        "screen_inch": 15.6,
        "battery_hours": 8.0,
    },
    "designer": {
        "processor_tier": 7,
        "ram_gb": 16,
        "storage_gb": 1024,
        "vga_type": "dedicated",
        "screen_inch": 15.6,
        "battery_hours": 8.0,
    },
    "business_analyst": {
        "processor_tier": 5,
        "ram_gb": 16,
        "storage_gb": 512,
        "vga_type": "integrated",
        "screen_inch": 14.0,
        "battery_hours": 12.0,
    },
    "manajemen": {
        "processor_tier": 5,
        "ram_gb": 8,
        "storage_gb": 512,
        "vga_type": "integrated",
        "screen_inch": 14.0,
        "battery_hours": 12.0,
    },
}

# Fallback when a role has no profile (defensive; all choices are covered above).
DEFAULT_TARGET = {
    "processor_tier": 5,
    "ram_gb": 8,
    "storage_gb": 512,
    "vga_type": "integrated",
    "screen_inch": 14.0,
    "battery_hours": 8.0,
}


def target_for(role):
    return ROLE_TARGETS.get(role, DEFAULT_TARGET)
