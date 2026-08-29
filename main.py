import requests
import pandas as pd
import time
from urllib.parse import urlsplit, urlunsplit


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = "95f00c7673e4489654f0505d771bc9db4a4554c0"

SERPER_URL = "https://google.serper.dev/search"

COUNTRY = "de"
LANGUAGE = "de"

RESULTS_PER_DORK = 10

DELAY_BETWEEN_SEARCHES = 1.0

INPUT_FILE = "dorks.txt"

OUTPUT_CSV = "results.csv"
OUTPUT_EXCEL = "results.xlsx"


# ============================================================
# LOAD DORKS
# ============================================================

def load_dorks(filename):

    with open(filename, "r", encoding="utf-8") as file:

        dorks = []

        for line in file:

            line = line.strip()

            # Ignore empty lines
            if not line:
                continue

            # Ignore comments
            if line.startswith("#"):
                continue

            dorks.append(line)

    # Remove duplicate dorks
    dorks = list(dict.fromkeys(dorks))

    return dorks


# ============================================================
# NORMALIZE URL
# ============================================================

def normalize_url(url):

    try:

        parsed = urlsplit(url)

        scheme = parsed.scheme.lower()

        domain = parsed.netloc.lower()

        path = parsed.path.rstrip("/")

        if not path:
            path = "/"

        # Remove fragment
        return urlunsplit(
            (
                scheme,
                domain,
                path,
                parsed.query,
                ""
            )
        )

    except Exception:

        return url


# ============================================================
# SEARCH SERPER
# ============================================================

def search_serper(query):

    headers = {

        "X-API-KEY": API_KEY,

        "Content-Type": "application/json"
    }

    payload = {

        "q": query,

        "gl": COUNTRY,

        "hl": LANGUAGE,

        "num": RESULTS_PER_DORK
    }

    response = requests.post(

        SERPER_URL,

        headers=headers,

        json=payload,

        timeout=30
    )

    # Check HTTP status

    if response.status_code != 200:

        raise Exception(

            f"Serper error {response.status_code}: "
            f"{response.text}"
        )

    return response.json()


# ============================================================
# EXTRACT ORGANIC RESULTS
# ============================================================

def extract_results(data, dork):

    results = []

    organic = data.get("organic", [])

    for item in organic:

        url = item.get("link", "")

        if not url:
            continue

        result = {

            "dork": dork,

            "position":
                item.get("position", ""),

            "title":
                item.get("title", ""),

            "url":
                url,

            "snippet":
                item.get("snippet", ""),

            "source":
                item.get("source", ""),

            "date":
                item.get("date", "")
        }

        results.append(result)

    return results


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("        DORK ENGINE - SERPER RUNNER")
    print("=" * 60)
    print()

    # --------------------------------------------------------
    # Load dorks
    # --------------------------------------------------------

    dorks = load_dorks(INPUT_FILE)

    if not dorks:

        print("ERROR: No dorks found.")

        return

    print(f"Dorks loaded: {len(dorks)}")

    print(
        f"Maximum SERP results: "
        f"{len(dorks) * RESULTS_PER_DORK}"
    )

    print()

    # --------------------------------------------------------
    # Run searches
    # --------------------------------------------------------

    all_results = []

    for index, dork in enumerate(dorks, start=1):

        print(
            f"[{index}/{len(dorks)}] "
            f"Searching:"
        )

        print(dork)

        try:

            data = search_serper(dork)

            results = extract_results(
                data,
                dork
            )

            all_results.extend(results)

            print(
                f"    Results: {len(results)}"
            )

        except Exception as error:

            print(
                f"    ERROR: {error}"
            )

        # Wait before next request

        if index < len(dorks):

            time.sleep(
                DELAY_BETWEEN_SEARCHES
            )

    # --------------------------------------------------------
    # No results
    # --------------------------------------------------------

    if not all_results:

        print()
        print("No results returned.")

        return

    # --------------------------------------------------------
    # Create dataframe
    # --------------------------------------------------------

    df = pd.DataFrame(all_results)

    print()
    print("=" * 60)

    print(
        f"Raw results: {len(df)}"
    )

    # --------------------------------------------------------
    # Normalize URLs
    # --------------------------------------------------------

    df["normalized_url"] = (

        df["url"]
        .apply(normalize_url)
    )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    unique_df = (

        df
        .drop_duplicates(
            subset=["normalized_url"]
        )
        .copy()
    )

    # Remove internal column

    unique_df = unique_df.drop(
        columns=["normalized_url"]
    )

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    unique_df.to_csv(

        OUTPUT_CSV,

        index=False,

        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # Save Excel
    # --------------------------------------------------------

    unique_df.to_excel(

        OUTPUT_EXCEL,

        index=False
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    print(
        f"Unique URLs: {len(unique_df)}"
    )

    print()

    print(
        f"Saved:"
    )

    print(
        f"  {OUTPUT_CSV}"
    )

    print(
        f"  {OUTPUT_EXCEL}"
    )

    print()

    print("=" * 60)

    print("DONE")

    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()