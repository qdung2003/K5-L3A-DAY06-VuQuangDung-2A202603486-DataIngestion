"""Author the fixed benchmark from source evidence before retrieval."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "starter"))
from src.evaluation import canonical

# Explicitly authored questions and evidence, never derived from retrieval output.
ITEMS = [
("dev", "direct", "Which loop does a break statement exit when loops are nested?",
 "The innermost enclosing for or while loop.",
 "The break statement breaks out of the innermost enclosing for or while loop", None),
("dev", "condition", "In the controlflow chapter, when is a loop's else clause skipped if execution ends early?",
 "A break skips it; return or a raised exception also skip it.",
 "In either kind of loop, the else clause is **not** executed if the loop was terminated by a break. Of course, other ways of ending the loop early, such as a return or a raised exception, will also skip execution of the else clause.", {"section":"controlflow"}),
("dev", "condition", "Why can a mutable default argument preserve changes between calls?",
 "The default is evaluated only once, so a mutable object can be shared between calls.",
 "**Important warning:** The default value is evaluated only once. This makes a difference when the default is a mutable object such as a list, dictionary, or instances of most classes.", None),
("dev", "direct", "How do you mark function parameters as positional-only and what calling restriction applies?",
 "Place them before /; they cannot be passed by keyword.",
 "If *positional-only*, the parameters' order matters, and the parameters cannot be passed by keyword. Positional-only parameters are placed before a / (forward-slash).", None),
("dev", "metadata", "In datastructures, which container is recommended for a queue needing fast operations at both ends?",
 "collections.deque, designed for fast appends and pops at both ends.",
 "To implement a queue, use collections.deque which was designed to have fast appends and pops from both ends.", {"section":"datastructures"}),
("dev", "paraphrase", "What punctuation is essential to construct a tuple containing just one value?",
 "A trailing comma; parentheses alone are insufficient.",
 "a tuple with one item is constructed by following a value with a comma (it is not sufficient to enclose a single value in parentheses).", None),
("dev", "condition", "How do you create an empty set, and why does {} not work?",
 "Use set(); {} creates an empty dictionary.",
 "to create an empty set you have to use set(), not {}; the latter creates an empty dictionary", None),
("dev", "direct", "In what order does list(d) return dictionary keys, and how do you get them sorted?",
 "Insertion order; use sorted(d) for sorted keys.",
 "Performing list(d) on a dictionary returns a list of all the keys used in the dictionary, in insertion order (if you want it sorted, just use sorted(d) instead).", None),
("dev", "condition", "Which names are excluded by from fibo import *?",
 "Names beginning with an underscore.",
 "This imports all names except those beginning with an underscore (_).", None),
("dev", "paraphrase", "How can I reload a changed module during an interactive interpreter session?",
 "Use importlib.reload(modulename), or restart the interpreter.",
 "if you change your modules, you must restart the interpreter -- or, if it's just one module you want to test interactively, use importlib.reload", None),
("dev", "direct", "What value is assigned to __name__ when a Python module is run as a script?",
 "__main__.",
 "the code in the module will be executed, just as if you imported it, but with the __name__ set to \"__main__\".", None),
("dev", "condition", "Why use with when working with file objects if an exception may occur?",
 "It properly closes the file after the suite, even if an exception is raised.",
 "It is good practice to use the with keyword when dealing with file objects. The advantage is that the file is properly closed after its suite finishes, even if an exception is raised at some point.", None),
("dev", "condition", "What happens if size is omitted or negative in f.read(size)?",
 "The entire file contents are read and returned, which may exceed available memory.",
 "When *size* is omitted or negative, the entire contents of the file will be read and returned; it's your problem if the file is twice as large as your machine's memory.", None),
("dev", "direct", "Which encoding should be used when opening a JSON file as text?",
 "UTF-8 for both reading and writing.",
 "JSON files must be encoded in UTF-8. Use encoding=\"utf-8\" when opening JSON file as a text file for both of reading and writing.", None),
("dev", "metadata", "In the errors chapter, where is a try statement's optional else clause placed, and when is it useful?",
 "After all except clauses; for code executed when the try clause raises no exception.",
 "The try ... except statement has an optional *else clause*, which, when present, must follow all *except clauses*. It is useful for code that must be executed if the *try clause* does not raise an exception.", {"section":"errors"}),
("test", "paraphrase", "How do instance variables differ from class variables in terms of sharing?",
 "Instance variables are unique to an instance; class variables are shared by all instances.",
 "Generally speaking, instance variables are for data unique to each instance and class variables are for attributes and methods shared by all instances of the class", None),
("test", "condition", "If both try and finally return values, which return value does the caller receive?",
 "The value returned by finally.",
 "If a finally clause includes a return statement, the returned value will be the one from the finally clause's return statement, not the value from the try clause's return statement.", None),
("test", "condition", "Are single-underscore attributes enforced private, and how should _spam be treated?",
 "No enforced private instance variables; a leading underscore signals a non-public implementation detail.",
 "\"Private\" instance variables that cannot be accessed except from inside an object don't exist in Python. However, there is a convention that is followed by most Python code: a name prefixed with an underscore (e.g. _spam) should be treated as a non-public part of the API", None),
("test", "metadata", "In stdlib2, what approach is preferred for coordinating threads sharing a resource?",
 "Concentrate all access to the resource in one thread and feed it requests through the queue module.",
 "the preferred approach to task coordination is to concentrate all access to a resource in a single thread and then use the queue module to feed that thread with requests from other threads.", {"section":"stdlib2"}),
("test", "metadata", "In stdlib2, where are log messages sent in the simplest logging setup?",
 "To a file or sys.stderr.",
 "At its simplest, log messages are sent to a file or to sys.stderr", {"section":"stdlib2"}),
]


def main():
    folder = ROOT / "benchmark"
    folder.mkdir(exist_ok=True)
    target = folder / "questions.json"
    if target.exists():
        raise SystemExit("Benchmark already exists. Do not overwrite a frozen benchmark.")
    pages = [json.loads(line) for line in (ROOT / "data/pages.jsonl").read_text(encoding="utf-8").splitlines()]
    questions = []
    for i, (split, category, question, answer, quote, filters) in enumerate(ITEMS, 1):
        matches = [p for p in pages if canonical(quote) in canonical(p["text"])
                   and (not filters or all(p["metadata"].get(k) == v for k, v in filters.items()))]
        if not matches:
            raise ValueError(f"Evidence missing for Q{i:02d}: {quote}")
        page = matches[0]
        questions.append({"id": f"Q{i:02d}", "split": split, "category": category,
            "question": question, "expected_answer": answer, "gold_source_id": page["document_id"],
            "gold_page": page["page"], "evidence_quote": quote, "filter": filters,
            "alternative_gold": [{"source_id": p["document_id"], "page": p["page"], "evidence_quote": quote}
                                 for p in matches[1:]]})
    target.write_text(json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lock = {"frozen_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "pages_sha256": hashlib.sha256((ROOT / "data/pages.jsonl").read_bytes()).hexdigest(),
        "split_rule": "Authored Q01-Q15 dev; Q16-Q20 test with different question topics. Shared chapters; not document-disjoint. No retrieval performed before freeze.",
        "selection_rule": "Max dev Evidence Hit@3, then dev Hit@1; if tied prefer B, C, A in that order (B simpler than filtering and structurally aware). No test-based tuning.",
        "coherence_sampling": "First 10 page IDs in lexicographic order; midpoint character of each unit. Choose earliest-starting chunk containing that position. Frozen before retrieval.",
        "filter_origin": "The chapter is explicitly named in each filtered question. No gold IDs or answers supplied to the retrieval function."}
    (folder / "freeze.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")
    print("Frozen 20 questions: 15 dev / 5 test; 5 filtered questions including 2 test.")


if __name__ == "__main__":
    main()
