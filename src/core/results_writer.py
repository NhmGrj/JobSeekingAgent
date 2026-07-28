import os
from datetime import datetime

VERDICT_ORDER = ["POSTULER", "PEUT-ÊTRE", "IGNORER", "ERREUR"]


def write_markdown(user_id: str, evaluated: list[dict], out_dir: str = "../results") -> str:
    """evaluated items: {subject, summary, url, score, verdict, explanation}"""
    os.makedirs(out_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    path = os.path.join(out_dir, f"{user_id}_{date_str}.md")

    with open(path, "w") as f:
        f.write(f"# Résultats du {datetime.now().strftime('%d/%m/%Y %H:%M')} — {user_id}\n\n")
        for verdict in VERDICT_ORDER:
            entries = [e for e in evaluated if e["verdict"] == verdict]
            if not entries:
                continue
            f.write(f"## {verdict}\n\n")
            for e in entries:
                f.write(f"### {e['summary']}\n")
                f.write(f"- **Sujet:** {e['subject']}\n")
                f.write(f"- **Score:** {e['score']}/10\n")
                f.write(f"- **Analyse:** {e['explanation']}\n")
                f.write(f"- **URL:** {e['url']}\n\n")

    return path
