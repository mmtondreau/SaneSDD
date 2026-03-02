"""Tests for design domain management."""

from __future__ import annotations

import shutil
from pathlib import Path

from sdd.design_manager import DesignManager

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDomainOperations:
    def test_list_domains_empty(self, tmp_project: Path) -> None:
        mgr = DesignManager(tmp_project)
        assert mgr.list_domains() == []

    def test_list_domains(self, tmp_project: Path) -> None:
        mgr = DesignManager(tmp_project)
        domain_dir = tmp_project / "design" / "DOMAIN_001_commerce"
        domain_dir.mkdir(parents=True)
        shutil.copy(FIXTURES_DIR / "sample_domain.md", domain_dir / "domain.md")

        domains = mgr.list_domains()
        assert len(domains) == 1
        assert domains[0].name == "DOMAIN_001_commerce"

    def test_find_domain_by_substring(self, tmp_project: Path) -> None:
        mgr = DesignManager(tmp_project)
        (tmp_project / "design" / "DOMAIN_001_commerce").mkdir(parents=True)

        result = mgr.find_domain("commerce")
        assert result is not None
        assert result.name == "DOMAIN_001_commerce"

    def test_find_domain_not_found(self, tmp_project: Path) -> None:
        mgr = DesignManager(tmp_project)
        assert mgr.find_domain("nonexistent") is None

    def test_next_domain_number_empty(self, tmp_project: Path) -> None:
        mgr = DesignManager(tmp_project)
        assert mgr.next_domain_number() == 1

    def test_next_domain_number_existing(self, tmp_project: Path) -> None:
        mgr = DesignManager(tmp_project)
        (tmp_project / "design" / "DOMAIN_001_commerce").mkdir(parents=True)
        (tmp_project / "design" / "DOMAIN_002_auth").mkdir(parents=True)
        assert mgr.next_domain_number() == 3

    def test_list_components_in_domain(self, tmp_project: Path) -> None:
        mgr = DesignManager(tmp_project)
        domain_dir = tmp_project / "design" / "DOMAIN_001_commerce"
        domain_dir.mkdir(parents=True)
        (domain_dir / "COMP_cart.md").write_text("# Cart Component\n")
        (domain_dir / "COMP_order.md").write_text("# Order Component\n")

        comps = mgr.list_components(domain_dir)
        assert len(comps) == 2
        assert comps[0].name == "COMP_cart.md"
        assert comps[1].name == "COMP_order.md"

    def test_list_components_all(self, tmp_project: Path) -> None:
        mgr = DesignManager(tmp_project)
        # Component inside a domain
        domain_dir = tmp_project / "design" / "DOMAIN_001_commerce"
        domain_dir.mkdir(parents=True)
        (domain_dir / "COMP_cart.md").write_text("# Cart\n")

        # Legacy top-level component
        (tmp_project / "design" / "COMP_legacy.md").write_text("# Legacy\n")

        comps = mgr.list_components()
        assert len(comps) == 2
        assert any("COMP_cart" in c.name for c in comps)
        assert any("COMP_legacy" in c.name for c in comps)

    def test_get_design_summary_with_domains(self, tmp_project: Path) -> None:
        mgr = DesignManager(tmp_project)
        (tmp_project / "design" / "design.md").write_text("# System Design\n")

        domain_dir = tmp_project / "design" / "DOMAIN_001_commerce"
        domain_dir.mkdir(parents=True)
        (domain_dir / "domain.md").write_text("# Commerce Domain\n")
        (domain_dir / "COMP_cart.md").write_text("# Cart\n")

        summary = mgr.get_design_summary()
        assert "System Design" in summary
        assert "Commerce Domain" in summary
        assert "Cart" in summary

    def test_no_design_dir(self, tmp_path: Path) -> None:
        mgr = DesignManager(tmp_path)
        assert mgr.list_domains() == []
        assert mgr.find_domain("anything") is None
        assert mgr.next_domain_number() == 1
        assert mgr.list_components() == []
