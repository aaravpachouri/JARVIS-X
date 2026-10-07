from __future__ import annotations

import re

from urllib.parse import (
    urlparse,
)


############################################################
# WEBSITE MATCHER
############################################################

class WebsiteMatcher:

    ########################################################
    # MATCH
    ########################################################

    def match(
        self,
        business_name: str,
        results: list[dict],
    ) -> dict:

        if not str(
            business_name or ""
        ).strip():

            return {
                "matched": False,
                "url": "",
                "confidence": 0.0,
                "reason": "Business name is missing.",
            }

        if not results:

            return {
                "matched": False,
                "url": "",
                "confidence": 0.0,
                "reason": "No search results found.",
            }

        ####################################################
        # BUSINESS IDENTITY TOKENS
        ####################################################

        identity = (
            self._business_identity(
                business_name
            )
        )

        primary_tokens = identity[
            "primary_tokens"
        ]

        secondary_tokens = identity[
            "secondary_tokens"
        ]

        all_tokens = (
            primary_tokens
            +
            secondary_tokens
        )

        if not all_tokens:

            return {
                "matched": False,
                "url": "",
                "confidence": 0.0,
                "reason": (
                    "Business name did not contain "
                    "usable identifying terms."
                ),
            }

        candidates = []

        ####################################################
        # EVALUATE SEARCH RESULTS
        ####################################################

        for result in results:

            if not isinstance(
                result,
                dict,
            ):

                continue

            url = str(
                result.get(
                    "url",
                    "",
                )
                or ""
            ).strip()

            if not url:

                continue

            ################################################
            # DOCUMENTS
            ################################################

            if self._is_document_url(
                url
            ):

                continue

            ################################################
            # DOMAIN
            ################################################

            domain = self._domain(
                url
            )

            if not domain:

                continue

            ################################################
            # BLOCKED / DIRECTORY / SOCIAL
            ################################################

            if self._is_blocked_domain(
                domain
            ):

                continue

            ################################################
            # TEXT
            ################################################

            title = str(
                result.get(
                    "title",
                    "",
                )
                or ""
            ).strip()

            snippet = str(
                result.get(
                    "snippet",
                    "",
                )
                or ""
            ).strip()

            ################################################
            # SCORE
            ################################################

            score_data = self._score_candidate(
                primary_tokens=primary_tokens,
                secondary_tokens=secondary_tokens,
                title=title,
                snippet=snippet,
                domain=domain,
            )

            if score_data is None:

                continue

            candidates.append(
                {
                    "url": url,
                    "domain": domain,
                    "score": score_data["score"],
                    "domain_score": (
                        score_data["domain_score"]
                    ),
                    "primary_matches": (
                        score_data["primary_matches"]
                    ),
                    "secondary_matches": (
                        score_data["secondary_matches"]
                    ),
                    "title_matches": (
                        score_data["title_matches"]
                    ),
                    "snippet_matches": (
                        score_data["snippet_matches"]
                    ),
                }
            )

        ####################################################
        # NOTHING USABLE
        ####################################################

        if not candidates:

            return {
                "matched": False,
                "url": "",
                "confidence": 0.0,
                "reason": (
                    "No credible official-business "
                    "domain was identified."
                ),
            }

        ####################################################
        # BEST CANDIDATE
        ####################################################

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        best = candidates[0]

        ####################################################
        # CONFIDENCE
        ####################################################

        confidence = max(
            0.0,
            min(
                0.99,
                best["score"] / 100.0,
            ),
        )

        ####################################################
        # STRICT ACCEPTANCE
        #
        # A result must have:
        #
        # 1. strong business-domain relationship
        # 2. at least one primary business-name term
        # 3. enough total evidence
        ####################################################

        if not self._is_strong_official_match(
            candidate=best,
        ):

            return {
                "matched": False,
                "url": "",
                "confidence": confidence,
                "reason": (
                    "Search results were found, but "
                    "none could be confidently identified "
                    "as the official business website."
                ),
            }

        ####################################################
        # RETURN ROOT WEBSITE
        ####################################################

        official_url = (
            self._root_url(
                best["url"]
            )
        )

        return {
            "matched": True,
            "url": official_url,
            "confidence": confidence,
            "reason": (
                "A strong direct relationship was "
                "found between the business identity "
                "and the candidate domain."
            ),
        }

    ########################################################
    # BUSINESS IDENTITY
    ########################################################

    @classmethod
    def _business_identity(
        cls,
        business_name: str,
    ) -> dict:

        text = str(
            business_name or ""
        ).strip()

        ####################################################
        # SEPARATE BUSINESS FROM DOCTOR / OWNER
        #
        # Example:
        #
        # Mukta Homeopathy Clinic |
        # Dr. Aashish R. Singh
        #
        # Primary = Mukta Homeopathy Clinic
        # Secondary = Aashish Singh
        ####################################################

        pieces = re.split(
            r"\s*\|\s*|\s+[-–—]\s+",
            text,
            maxsplit=1,
        )

        primary_text = pieces[0].strip()

        secondary_text = ""

        if len(pieces) > 1:

            secondary_text = (
                pieces[1].strip()
            )

        primary_tokens = cls._tokens(
            primary_text
        )

        secondary_tokens = cls._person_tokens(
            secondary_text
        )

        ####################################################
        # If no explicit separator exists, use full name
        # as primary.
        ####################################################

        if not primary_tokens:

            primary_tokens = cls._tokens(
                text
            )

        return {
            "primary_tokens": primary_tokens,
            "secondary_tokens": secondary_tokens,
        }

    ########################################################
    # TOKENIZE BUSINESS NAME
    ########################################################

    @staticmethod
    def _tokens(
        text: str,
    ) -> list[str]:

        words = re.findall(
            r"[a-z0-9]+",
            str(
                text or ""
            ).lower(),
        )

        ignored = {

            "the",
            "and",
            "of",
            "for",
            "with",
            "near",
            "at",
            "in",

            "pvt",
            "private",
            "ltd",
            "limited",
            "llp",
            "inc",
            "incorporated",

            "company",
            "co",
            "corporation",

            "shop",
            "store",
            "services",
            "service",
            "centre",
            "center",

            "clinic",
            "hospital",
            "medical",

            "university",
            "college",
            "school",
            "academy",

            "dr",
            "doctor",
            "mr",
            "mrs",
            "ms",
            "prof",
        }

        return [
            word
            for word in words
            if (
                len(word) >= 4
                and
                word not in ignored
            )
        ]

    ########################################################
    # PERSON TOKENS
    ########################################################

    @staticmethod
    def _person_tokens(
        text: str,
    ) -> list[str]:

        words = re.findall(
            r"[a-z0-9]+",
            str(
                text or ""
            ).lower(),
        )

        ignored = {
            "dr",
            "doctor",
            "mr",
            "mrs",
            "ms",
            "prof",
            "md",
            "mbbs",
            "owner",
            "founder",
        }

        return [
            word
            for word in words
            if (
                len(word) >= 5
                and
                word not in ignored
            )
        ]

    ########################################################
    # SCORE CANDIDATE
    ########################################################

    def _score_candidate(
        self,
        primary_tokens: list[str],
        secondary_tokens: list[str],
        title: str,
        snippet: str,
        domain: str,
    ) -> dict | None:

        domain_compact = re.sub(
            r"[^a-z0-9]",
            "",
            domain.lower(),
        )

        domain_words = re.findall(
            r"[a-z0-9]+",
            domain.lower().replace(
                "-",
                " ",
            ),
        )

        ####################################################
        # PRIMARY DOMAIN MATCHES
        ####################################################

        primary_matches = 0

        for token in primary_tokens:

            if token in domain_words:

                primary_matches += 1

                continue

            if (
                len(token) >= 6
                and token in domain_compact
            ):

                primary_matches += 1

        ####################################################
        # SECONDARY / PERSON MATCHES
        #
        # Person-name matches alone are NEVER enough.
        ####################################################

        secondary_matches = 0

        for token in secondary_tokens:

            if token in domain_words:

                secondary_matches += 1

                continue

            if (
                len(token) >= 7
                and token in domain_compact
            ):

                secondary_matches += 1

        ####################################################
        # TITLE
        ####################################################

        title_text = title.lower()

        title_matches = sum(
            1
            for token in primary_tokens
            if token in title_text
        )

        ####################################################
        # SNIPPET
        ####################################################

        snippet_text = snippet.lower()

        snippet_matches = sum(
            1
            for token in primary_tokens
            if token in snippet_text
        )

        ####################################################
        # DOMAIN SCORE
        ####################################################

        domain_score = 0.0

        if primary_tokens:

            primary_ratio = (
                primary_matches
                /
                len(primary_tokens)
            )

            domain_score += (
                primary_ratio
                * 65.0
            )

        ####################################################
        # EXACT COMPACT BUSINESS NAME
        ####################################################

        compact_primary = re.sub(
            r"[^a-z0-9]",
            "",
            "".join(
                primary_tokens
            ),
        )

        if (
            len(compact_primary) >= 7
            and
            compact_primary in domain_compact
        ):

            domain_score += 25.0

        ####################################################
        # TITLE SUPPORT
        ####################################################

        if primary_tokens:

            title_ratio = (
                title_matches
                /
                len(primary_tokens)
            )

            domain_score += (
                title_ratio
                * 7.0
            )

        ####################################################
        # SNIPPET SUPPORT
        ####################################################

        if primary_tokens:

            snippet_ratio = (
                snippet_matches
                /
                len(primary_tokens)
            )

            domain_score += (
                snippet_ratio
                * 3.0
            )

        ####################################################
        # PERSON-ONLY PENALTY
        #
        # This is critical for cases such as:
        #
        # "Mukta Homeopathy Clinic |
        #  Dr. Aashish R. Singh"
        #
        # A domain containing "aashishsingh" but no
        # "mukta" / "homeopathy" should be rejected.
        ####################################################

        if (
            secondary_matches > 0
            and
            primary_matches == 0
        ):

            return None

        ####################################################
        # DOMAIN REQUIRES BUSINESS EVIDENCE
        ####################################################

        if primary_matches == 0:

            return None

        ####################################################
        # TITLE / SNIPPET
        ####################################################

        score = (
            domain_score
        )

        ####################################################
        # OFFICIAL LANGUAGE
        ####################################################

        title_lower = (
            title.lower()
        )

        if any(
            phrase in title_lower
            for phrase in (
                "official website",
                "official site",
                "welcome to",
            )
        ):

            score += 5.0

        ####################################################
        # CAP
        ####################################################

        score = min(
            100.0,
            score,
        )

        return {
            "score": score,
            "domain_score": domain_score,
            "primary_matches": primary_matches,
            "secondary_matches": secondary_matches,
            "title_matches": title_matches,
            "snippet_matches": snippet_matches,
        }

    ########################################################
    # STRICT OFFICIAL CHECK
    ########################################################

    @staticmethod
    def _is_strong_official_match(
        candidate: dict,
    ) -> bool:

        primary_matches = int(
            candidate.get(
                "primary_matches",
                0,
            )
        )

        domain_score = float(
            candidate.get(
                "domain_score",
                0.0,
            )
        )

        score = float(
            candidate.get(
                "score",
                0.0,
            )
        )

        title_matches = int(
            candidate.get(
                "title_matches",
                0,
            )
        )

        ####################################################
        # ABSOLUTE REQUIREMENT:
        #
        # At least one primary business token must match.
        ####################################################

        if primary_matches <= 0:

            return False

        ####################################################
        # Strong direct business domain.
        ####################################################

        if (
            domain_score >= 65.0
            and
            score >= 70.0
        ):

            return True

        ####################################################
        # Multiple business terms + supporting title.
        ####################################################

        if (
            primary_matches >= 2
            and
            domain_score >= 55.0
            and
            title_matches >= 1
            and
            score >= 65.0
        ):

            return True

        return False

    ########################################################
    # DOCUMENT URL
    ########################################################

    @staticmethod
    def _is_document_url(
        url: str,
    ) -> bool:

        try:

            path = (
                urlparse(
                    url
                )
                .path
                .lower()
            )

        except Exception:

            return True

        blocked_extensions = (
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".zip",
            ".rar",
            ".txt",
            ".csv",
        )

        return path.endswith(
            blocked_extensions
        )

    ########################################################
    # ROOT URL
    ########################################################

    @staticmethod
    def _root_url(
        url: str,
    ) -> str:

        try:

            parsed = urlparse(
                url
            )

            if not parsed.scheme:

                return url

            return (
                f"{parsed.scheme}://"
                f"{parsed.netloc}/"
            )

        except Exception:

            return url

    ########################################################
    # DOMAIN
    ########################################################

    @staticmethod
    def _domain(
        url: str,
    ) -> str:

        try:

            parsed = urlparse(
                url
            )

            return (
                parsed.netloc
                .lower()
                .split(":")[0]
                .removeprefix(
                    "www."
                )
            )

        except Exception:

            return ""

    ########################################################
    # BLOCKED DOMAINS
    ########################################################

    @staticmethod
    def _is_blocked_domain(
        domain: str,
    ) -> bool:

        blocked = {

            ################################################
            # SEARCH
            ################################################

            "google.com",
            "google.co.in",
            "googleusercontent.com",
            "bing.com",
            "duckduckgo.com",
            "search.yahoo.com",
            "yahoo.com",

            ################################################
            # SOCIAL
            ################################################

            "facebook.com",
            "instagram.com",
            "youtube.com",
            "linkedin.com",
            "x.com",
            "twitter.com",
            "threads.net",

            ################################################
            # BUSINESS DIRECTORIES
            ################################################

            "justdial.com",
            "sulekha.com",
            "yelp.com",
            "yellowpages.com",
            "tripadvisor.com",
            "indiamart.com",
            "tradeindia.com",
            "asklaila.com",
            "nearbuy.com",
            "zaubacorp.com",
            "fundoodata.com",
            "ambitionbox.com",
            "crunchbase.com",

            ################################################
            # HEALTH / DOCTOR DIRECTORIES
            ################################################

            "practo.com",
            "lybrate.com",
            "credihealth.com",
            "clinicspots.com",
            "hexahealth.com",
            "mfine.co",
            "docprime.com",
            "apollo247.com",

            ################################################
            # EDUCATION
            ################################################

            "shiksha.com",
            "collegedunia.com",
            "careers360.com",
            "getmyuni.com",
            "collegedekho.com",

            ################################################
            # REFERENCE
            ################################################

            "wikipedia.org",
            "wikidata.org",

            ################################################
            # MAPS / LOCAL RESULTS
            ################################################

            "mapquest.com",
            "mapcarta.com",
            "mappls.com",
        }

        normalized = (
            str(
                domain or ""
            ).lower()
            .strip()
        )

        return any(
            normalized == blocked_domain
            or normalized.endswith(
                "." + blocked_domain
            )
            for blocked_domain in blocked
        )