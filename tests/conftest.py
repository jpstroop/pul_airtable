"""Pytest fixtures for pul_airtable tests."""

# Standard library imports
from typing import Dict

# Third party imports
import pytest


@pytest.fixture
def sample_pula_staff_row() -> Dict[str, str]:
    """Sample CSV row for a PULA staff member."""
    return {
        "Emplid": "123456789",
        "Preferred Else Primary First Name": "Alex",
        "Preferred Else Primary Last Name": "Smith",
        "E-Mail Address - Campus": "asmith@princeton.edu",
        "Net ID": "asmith",
        "Position Number": "00012345",
        "Union Code": "LIB",
        "Sal Plan Descr": "Library Support Staff",
        "Sal Plan": "LS",
        "Department Name": "Lib-Collections & Access Svcs",
        "Dept": "31200",
        "Position - Job Title": "Library Assistant",
        "Grade": "7",
        "FTE": "1.0",
        "Hire Date": "1/15/2020",
        "Rehire Date": "1/15/2020",
        "Status": "Active",
        "Staff": "Regular",
        "Manager/Supervisor Emplid": "987654321",
    }


@pytest.fixture
def sample_dof_librarian_row() -> Dict[str, str]:
    """Sample CSV row for a DoF Librarian."""
    return {
        "Emplid": "234567890",
        "Preferred Else Primary First Name": "Jordan",
        "Preferred Else Primary Last Name": "Lee",
        "E-Mail Address - Campus": "jlee@princeton.edu",
        "Net ID": "jlee",
        "Sal Plan Descr": "Regular Professional Library",
        "Sal Plan": "LR",
        "Department Name": "Lib-Data, Rsrch&Teaching Svcs",
        "Dept": "31300",
        "Admin Post Title": "Data Services Librarian",
        "Position - Job Title": "Librarian",
        "FTE": "1.0",
        "Hire Date": "7/1/2018",
        "Rehire Date": "7/1/2018",
        "Status": "Active",
        "Staff": "Regular",
        "Manager/Supervisor Emplid": "987654321",
    }


@pytest.fixture
def sample_dof_specialist_row() -> Dict[str, str]:
    """Sample CSV row for a DoF Professional Specialist."""
    return {
        "Emplid": "345678901",
        "Preferred Else Primary First Name": "Taylor",
        "Preferred Else Primary Last Name": "Chen",
        "E-Mail Address - Campus": "tchen@princeton.edu",
        "Net ID": "tchen",
        "Sal Plan Descr": "Reg Prof Specialist",
        "Sal Plan": "PS",
        "Department Name": "Library-Special Collections",
        "Dept": "31400",
        "Position - Job Title": "Conservator",
        "FTE": "1.0",
        "Hire Date": "9/1/2019",
        "Rehire Date": "9/1/2019",
        "Status": "Active",
        "Staff": "Regular",
        "Manager/Supervisor Emplid": "987654321",
    }


@pytest.fixture
def sample_casual_row() -> Dict[str, str]:
    """Sample CSV row for a casual hourly employee."""
    return {
        "Emplid": "456789012",
        "Preferred Else Primary First Name": "Morgan",
        "Preferred Else Primary Last Name": "Davis",
        "E-Mail Address - Campus": "mdavis@princeton.edu",
        "Net ID": "mdavis",
        "Sal Plan Descr": "Casual Hourly",
        "Sal Plan": "CH",
        "Department Name": "Lib-Collections & Access Svcs",
        "Dept": "31200",
        "Position - Job Title": "Library Aide",
        "FTE": "0.5",
        "Hire Date": "1/5/2023",
        "Rehire Date": "1/5/2023",
        "Status": "Active",
        "Staff": "Casual Hourly",
        "Manager/Supervisor Emplid": "987654321",
    }


@pytest.fixture
def sample_on_leave_row() -> Dict[str, str]:
    """Sample CSV row for an HR employee on leave with pay."""
    return {
        "Emplid": "567890123",
        "Preferred Else Primary First Name": "Riley",
        "Preferred Else Primary Last Name": "Johnson",
        "E-Mail Address - Campus": "rjohnson@princeton.edu",
        "Net ID": "rjohnson",
        "Position Number": "00054321",
        "Union Code": "LIB",
        "Sal Plan Descr": "Library Support Staff",
        "Sal Plan": "LS",
        "Department Name": "Lib-Research Coll & Presr Cons",
        "Dept": "31500",
        "Position - Job Title": "Preservation Specialist",
        "FTE": "1.0",
        "Hire Date": "3/1/2015",
        "Rehire Date": "3/1/2015",
        "Status": "Leave With Pay",
        "Staff": "Regular",
        "Manager/Supervisor Emplid": "987654321",
    }
