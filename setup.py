from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).parent
INSTALL_REQUIRES = [
    line
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    if line and not line.startswith("#")
]


setup(
    name="support-router",
    version="0.2.0",
    description="Agent-harness-independent support email routing service",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Quintus S.",
    license="MIT",
    python_requires=">=3.10",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=INSTALL_REQUIRES,
    entry_points={
        "console_scripts": [
            "support-router=support_router.cli:main",
            "support-router-api=support_router.api:run",
        ]
    },
)
