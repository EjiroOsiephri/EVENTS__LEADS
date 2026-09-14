# All the search queries the system will run.
# Edit the lists below to change coverage.

CITIES = [
    "Lagos",
    "Ibadan",
    "Abeokuta",
    "Ogun State",
    "Osogbo",
    "Ilorin",
]

# Queries that get combined with each city above
CITY_TEMPLATES = [
    "{city} concert 2026 announcement",
    "{city} music festival 2026",
    "{city} conference 2026 tickets",
    "{city} exhibition 2026",
    "{city} trade fair 2026",
    "{city} brand activation event",
    "{city} product launch event 2026",
    "{city} corporate event 2026",
    "{city} awards night 2026",
    "{city} campus tour event",
    "{city} church convention 2026",
    "{city} political rally 2026",
    "{city} event centre upcoming events",
    "{city} save the date event 2026",
    "event production company {city}",
    "event planner {city} upcoming event",
]

# Queries that run on their own, no city inserted
GENERAL_QUERIES = [
    "Nigeria campus tour 2026 announcement",
    "Nigeria nationwide tour 2026 dates",
    "Nigeria brand activation agency upcoming campaign",
    "Nigeria experiential marketing agency event",
    "Nigeria concert lineup announced 2026",
    "Nigeria conference call for exhibitors 2026",
    "Nigeria event sponsorship opportunity 2026",
    "site:tix.africa Lagos 2026",
    "site:eventbrite.com Lagos Nigeria 2026",
    "site:instagram.com Lagos event 2026 coming soon",
]


def build_queries():
    """Returns the full list of search queries to run."""
    queries = []

    for city in CITIES:
        for template in CITY_TEMPLATES:
            queries.append(template.format(city=city))

    queries.extend(GENERAL_QUERIES)

    return queries


if __name__ == "__main__":
    all_queries = build_queries()
    print(f"Total queries: {len(all_queries)}")
    print()
    for q in all_queries[:10]:
        print(" ", q)
    print("  ...")