"""
Query Processing: Rewrites and expands user queries for better retrieval
Handles query variations, synonyms, and domain-specific terminology
"""

from typing import List
from utils.logger import logging


class QueryProcessor:
    """
    Processes user queries by rewriting and expanding them
    Improves retrieval by handling synonyms and query variations
    """
    
    # AWR-specific synonyms and query expansions
    QUERY_EXPANSIONS = {
        "wait events": ["wait events", "bottlenecks", "performance issues", "latency"],
        "cpu": ["cpu", "processor usage", "cpu utilization", "cpu consumption"],
        "db time": ["db time", "database time", "total elapsed time", "response time"],
        "sql": ["sql", "sql statements", "queries", "sql commands", "sql execution"],
        "index": ["index", "indexes", "indices", "indexing", "index scan"],
        "parsing": ["parsing", "hard parse", "soft parse", "parse calls", "parse ratio"],
        "io": ["i/o", "io", "disk read", "disk write", "disk io", "physical io"],
        "latch": ["latch", "latch contention", "latch wait", "latch free"],
        "lock": ["lock", "locks", "row lock", "lock contention", "enqueue"],
        "buffer": ["buffer", "buffer cache", "buffer hit", "cache hit ratio"],
        "memory": ["memory", "sga", "pga", "memory usage", "memory allocation"],
        "redo": ["redo", "redo log", "log file", "log writer"],
        "transaction": ["transaction", "txn", "commit", "rollback"],
        "session": ["session", "sessions", "user session", "database session"],
        "archive": ["archive", "archivelog", "archive mode", "archive log mode"],
        "optimizer": ["optimizer", "query optimizer", "execution plan", "explain plan"],
        "statistics": ["statistics", "table statistics", "column statistics", "stats"],
        "performance": ["performance", "performance issue", "performance problem", "slow query"]
    }
    
    def __init__(self):
        """Initialize query processor"""
        logging.info("QueryProcessor initialized")
    
    def rewrite_query(self, query: str) -> str:
        """
        Rewrite query for clarity and completeness
        
        Args:
            query: Original user query
        
        Returns:
            Rewritten query
        """
        rewritten = query.lower()
        
        # Expand abbreviations
        abbreviations = {
            "db ": "database ",
            "cpu ": "processor ",
            "io ": "input/output ",
            "sql ": "sql ",
            "txn ": "transaction ",
            "msg ": "message ",
            "sec ": "seconds ",
            "ms ": "milliseconds ",
        }
        
        for abbr, expansion in abbreviations.items():
            if abbr in rewritten:
                rewritten = rewritten.replace(abbr, expansion)
        
        logging.info(f"Rewritten query: {rewritten[:80]}...")
        
        return rewritten
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand single query into multiple query variations
        
        Args:
            query: Original user query
        
        Returns:
            List of expanded queries
        """
        queries = [query]
        query_lower = query.lower()
        
        # Find keywords and add related queries
        for keyword, synonyms in self.QUERY_EXPANSIONS.items():
            if keyword in query_lower:
                # Generate variations with synonyms
                for synonym in synonyms[1:]:  # Skip the keyword itself
                    expanded = query.replace(keyword, synonym, 1)
                    expanded = expanded.replace(keyword, synonym)  # Replace all occurrences
                    if expanded not in queries:
                        queries.append(expanded)
        
        # Add common follow-up questions
        if "what" in query_lower and "how" not in query_lower:
            how_query = query.replace("what", "how to fix").lower()
            if how_query not in queries:
                queries.append(how_query)
        
        if "identify" in query_lower:
            fix_query = query.replace("identify", "fix").lower()
            if fix_query not in queries:
                queries.append(fix_query)
        
        # Limit to 5 variations
        queries = queries[:5]
        
        logging.info(f"Generated {len(queries)} query variations")
        
        return queries
    
    def get_search_terms(self, query: str) -> List[str]:
        """
        Extract key search terms from query
        
        Args:
            query: User query
        
        Returns:
            List of important search terms
        """
        query_lower = query.lower()
        terms = []
        
        # Extract domain keywords
        for keyword in self.QUERY_EXPANSIONS.keys():
            if keyword in query_lower:
                terms.append(keyword)
        
        # Extract important words (nouns, verbs, adjectives)
        stop_words = {"the", "a", "an", "and", "or", "in", "at", "to", "for", "of", "is", "are", "this", "that"}
        words = query_lower.split()
        
        for word in words:
            word_clean = word.strip(".,!?;:")
            if len(word_clean) > 3 and word_clean not in stop_words:
                if word_clean not in terms:
                    terms.append(word_clean)
        
        logging.info(f"Extracted {len(terms)} search terms")
        
        return terms