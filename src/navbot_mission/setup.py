from glob import glob
from setuptools import find_packages, setup

package_name = "navbot_mission"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Nonso",
    maintainer_email="nonso@users.noreply.github.com",
    description="Mission scripts for the NavBot navigation demo.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "multi_goal_nav = navbot_mission.multi_goal_nav:main",
            "scan_frame_republisher = navbot_mission.scan_frame_republisher:main",
            "synthetic_scan_publisher = navbot_mission.synthetic_scan_publisher:main",
        ],
    },
)
