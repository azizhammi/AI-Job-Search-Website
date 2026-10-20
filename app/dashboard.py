
import httpx
import streamlit as st

API_BASE = "http://127.0.0.1:8000"
STATUSES = ["saved", "applied", "interview", "rejected", "offer"]

STATUS_LABELS = {
    "saved": "Saved",
    "applied": "Applied",
    "interview": "Interview",
    "rejected": "Rejected",
    "offer": "Offer",
}

st.set_page_config(
    page_title="My Job Search",
    page_icon="📋",
    layout="wide",
)


# --------------------------------------------------
# API HELPERS
# --------------------------------------------------

def api_get(path, params=None):
    response = httpx.get(
        f"{API_BASE}{path}",
        params=params,
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


def api_post(path, payload):
    response = httpx.post(
        f"{API_BASE}{path}",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def api_patch(path, payload):
    response = httpx.patch(
        f"{API_BASE}{path}",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def discover_jobs(limit, keyword):
    # Fetch external listings without saving them.
    return api_get(
        "/jobs/discover",
        {
            "limit": limit,
            "keyword": keyword.strip() or None,
        },
    )


def save_job(job):
    # Only called when the user clicks Save job.
    payload = {
        "title": job.get("title", "Untitled role"),
        "company": job.get("company", "Unknown company"),
        "location": job.get("location"),
        "description": job.get("description"),
        "url": str(job.get("url", "")),
        "source": job.get("source", "Arbeitnow"),
        "required_skills": job.get("required_skills") or [],
    }

    return api_post("/jobs", payload)


def show_error(action, exc):
    st.error(f"{action}: {exc}")

    if isinstance(exc, httpx.HTTPStatusError):
        st.caption(
            f"HTTP {exc.response.status_code}: "
            f"{exc.response.text[:400]}"
        )
    else:
        st.caption(
            "Check that the backend is running at "
            "http://127.0.0.1:8000."
        )


def load_data():
    dashboard = api_get("/dashboard")
    jobs = api_get("/jobs")

    if not isinstance(jobs, list):
        raise ValueError("The jobs API did not return a list.")

    return dashboard, jobs


def normalized_url(url):
    return str(url or "").strip().rstrip("/")


def get_match_map(dashboard):
    result = {}

    for item in dashboard.get("top_matches", []):
        job = item.get("job", {})
        job_id = job.get("id")

        if job_id is not None:
            result[job_id] = item.get("relevance", {})

    return result


def render_metrics(dashboard, jobs):
    counts = dashboard.get("status_counts", {})

    columns = st.columns(4)

    metrics = [
        ("Saved jobs", dashboard.get("total_jobs", len(jobs))),
        ("Applications sent", counts.get("applied", 0)),
        ("Interviews", counts.get("interview", 0)),
        ("Offers", counts.get("offer", 0)),
    ]

    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


def render_job(job, relevance=None, key_prefix="job"):
    relevance = relevance or {}

    with st.container(border=True):
        st.subheader(job.get("title") or "Untitled role")

        company = job.get("company") or "Company not specified"
        location = job.get("location") or "Location not specified"

        st.write(f"**{company}** · {location}")

        score = relevance.get("score")

        if score is not None:
            try:
                score = max(0, min(100, int(float(score))))
                st.progress(score / 100, text=f"Match score: {score}%")
            except (TypeError, ValueError):
                pass

        matched_skills = relevance.get("matched_skills", [])
        if matched_skills:
            st.caption("Matching skills: " + ", ".join(matched_skills))

        if job.get("description"):
            with st.expander("Read job description"):
                st.write(job["description"])

        skills = job.get("required_skills") or []
        if skills:
            st.caption("Required skills: " + ", ".join(skills))

        if job.get("url"):
            st.link_button(
                "View original listing",
                str(job["url"]),
                key=f"{key_prefix}-link",
            )


# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

with st.sidebar:
    st.title("My Job Search")
    st.caption("Find jobs and manage your applications.")

    page = st.radio(
        "Navigation",
        ["Overview", "Find jobs", "Applications"],
    )

    st.divider()
    st.caption("Job source: Arbeitnow")
    st.caption("Powered by FastAPI and SQLite")

    if st.button("Refresh data", use_container_width=True):
        st.rerun()


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

try:
    dashboard, jobs = load_data()
except (httpx.HTTPError, ValueError) as exc:
    st.title("My Job Search")
    st.error("We couldn't load your data.")
    show_error("Connection problem", exc)
    st.stop()

counts = dashboard.get("status_counts", {})
match_by_id = get_match_map(dashboard)

saved_urls = {
    normalized_url(job.get("url"))
    for job in jobs
    if job.get("url")
}


# --------------------------------------------------
# OVERVIEW
# --------------------------------------------------

if page == "Overview":
    st.title("Welcome to your job search")
    st.write(
        "Keep track of interesting roles, find new opportunities, "
        "and stay organised throughout your applications."
    )

    render_metrics(dashboard, jobs)

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Find your next opportunity")
        st.write(
            "Search job listings and choose which ones you want to save. "
            "Searching does not add anything to your collection."
        )

        if st.button(
            "Find jobs",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["navigation_page"] = "Find jobs"
            st.rerun()

    with right:
        st.subheader("Keep applications organised")
        st.write(
            "Update application statuses and keep notes about interviews "
            "and follow-ups."
        )

        if st.button(
            "View applications",
            use_container_width=True,
        ):
            st.session_state["navigation_page"] = "Applications"
            st.rerun()

    # Streamlit radio navigation uses session state for its selected value.
    requested_page = st.session_state.pop("navigation_page", None)
    if requested_page:
        st.info(
            f"Choose **{requested_page}** from the sidebar to continue."
        )

    st.divider()
    st.subheader("Recommended jobs")

    recommendations = dashboard.get("top_matches", [])

    if not recommendations:
        st.info(
            "No recommendations yet. Find a job and save it to start "
            "building your collection."
        )
    else:
        for item in recommendations[:5]:
            job = item.get("job", {})
            relevance = item.get("relevance", {})

            render_job(
                job,
                relevance,
                key_prefix=f"recommendation-{job.get('id')}",
            )

    st.divider()
    st.subheader("Recently saved")

    recent_jobs = sorted(
        jobs,
        key=lambda item: item.get("id", 0),
        reverse=True,
    )[:5]

    if not recent_jobs:
        st.caption("You haven't saved any jobs yet.")
    else:
        for job in recent_jobs:
            render_job(
                job,
                match_by_id.get(job.get("id"), {}),
                key_prefix=f"recent-{job.get('id')}",
            )


# --------------------------------------------------
# FIND JOBS
# --------------------------------------------------

elif page == "Find jobs":
    st.title("Find jobs")
    st.write(
        "Search external job listings. Review a role before saving it "
        "to your personal collection."
    )

    st.info(
        "Searching never saves a job automatically. "
        "Use the Save job button only for roles you want to keep."
    )

    with st.form("job_search_form"):
        keyword = st.text_input(
            "Job title or keyword",
            placeholder="e.g. Python developer, data analyst",
        )

        limit = st.selectbox(
            "Number of listings",
            [10, 20, 30, 50],
            index=1,
        )

        search_submitted = st.form_submit_button(
            "Search jobs",
            type="primary",
            use_container_width=True,
        )

    if search_submitted:
        try:
            with st.spinner("Searching for jobs..."):
                results = discover_jobs(limit, keyword)

            if not isinstance(results, list):
                st.error("Unexpected response from the job search API.")
            else:
                st.session_state["discovered_jobs"] = results
                st.session_state["last_keyword"] = keyword
                st.success(f"Found {len(results)} job listing(s).")

        except (httpx.HTTPError, ValueError) as exc:
            show_error("Job search failed", exc)

    results = st.session_state.get("discovered_jobs", [])

    if results:
        st.divider()
        st.subheader("Search results")

        filter_text = st.text_input(
            "Filter results",
            placeholder="Company, title, or location",
            key="filter_discovered_jobs",
        )

        visible_results = []

        for job in results:
            searchable = " ".join([
                str(job.get("title", "")),
                str(job.get("company", "")),
                str(job.get("location", "")),
                str(job.get("description", "")),
            ]).casefold()

            if filter_text.strip().casefold() in searchable:
                visible_results.append(job)

        st.caption(f"{len(visible_results)} result(s)")

        for index, job in enumerate(visible_results):
            url = normalized_url(job.get("url"))
            already_saved = url in saved_urls

            with st.container(border=True):
                st.subheader(job.get("title") or "Untitled role")
                st.write(
                    f"**{job.get('company') or 'Company not specified'}** · "
                    f"{job.get('location') or 'Location not specified'}"
                )

                if job.get("source"):
                    st.caption(f"Source: {job['source']}")

                if job.get("description"):
                    with st.expander("Read job description"):
                        st.write(job["description"])

                required_skills = job.get("required_skills") or []
                if required_skills:
                    st.caption(
                        "Required skills: "
                        + ", ".join(required_skills)
                    )

                action_col, link_col = st.columns([1, 2])

                with action_col:
                    if already_saved:
                        st.success("Already saved")
                    elif st.button(
                        "Save job",
                        key=f"save-{index}-{url}",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            save_job(job)
                            st.success("Job saved to your collection.")
                            st.rerun()
                        except httpx.HTTPStatusError as exc:
                            if exc.response.status_code == 409:
                                st.info("This job is already saved.")
                                st.rerun()
                            else:
                                show_error("Could not save job", exc)
                        except (httpx.HTTPError, ValueError) as exc:
                            show_error("Could not save job", exc)

                with link_col:
                    if job.get("url"):
                        st.link_button(
                            "View original listing",
                            str(job["url"]),
                            key=f"external-{index}-{url}",
                        )

    else:
        st.caption(
            "Enter a keyword above and select Search jobs to see listings."
        )

    st.divider()
    st.subheader("Your saved jobs")

    if not jobs:
        st.write("No saved jobs yet.")
    else:
        saved_filter = st.text_input(
            "Search saved jobs",
            placeholder="Filter by job title, company, or location",
            key="filter_saved_jobs",
        )

        saved_results = [
            job for job in jobs
            if saved_filter.strip().casefold() in " ".join([
                str(job.get("title", "")),
                str(job.get("company", "")),
                str(job.get("location", "")),
            ]).casefold()
        ]

        for job in saved_results:
            with st.container(border=True):
                st.markdown(f"**{job.get('title', 'Untitled role')}**")
                st.write(
                    f"{job.get('company', 'Company not specified')} · "
                    f"{job.get('location') or 'Location not specified'}"
                )
                st.caption(
                    "Status: "
                    + STATUS_LABELS.get(
                        job.get("application_status", "saved"),
                        "Saved",
                    )
                )

                if job.get("url"):
                    st.link_button(
                        "View original listing",
                        job["url"],
                        key=f"saved-link-{job.get('id')}",
                    )


# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------

elif page == "Applications":
    st.title("My applications")
    st.write(
        "Keep your job search organised by tracking each role "
        "and recording your next steps."
    )

    render_metrics(dashboard, jobs)
    st.divider()

    if not jobs:
        st.info(
            "You don't have any saved jobs yet. Visit Find jobs and "
            "select Save job to add a role here."
        )
    else:
        filter_col, status_col = st.columns([2, 1])

        with filter_col:
            application_search = st.text_input(
                "Search applications",
                placeholder="Job title or company",
            )

        with status_col:
            selected_status = st.selectbox(
                "Application stage",
                ["all"] + STATUSES,
                format_func=lambda value: (
                    "All stages"
                    if value == "all"
                    else STATUS_LABELS[value]
                ),
            )

        visible_jobs = []

        for job in jobs:
            job_status = job.get("application_status", "saved")

            if selected_status != "all" and job_status != selected_status:
                continue

            searchable = " ".join([
                str(job.get("title", "")),
                str(job.get("company", "")),
                str(job.get("location", "")),
            ]).casefold()

            if application_search.strip().casefold() not in searchable:
                continue

            visible_jobs.append(job)

        visible_jobs.sort(
            key=lambda item: item.get("id", 0),
            reverse=True,
        )

        st.caption(f"{len(visible_jobs)} application(s)")

        for job in visible_jobs:
            job_id = job["id"]
            current_status = job.get("application_status", "saved")

            with st.container(border=True):
                st.subheader(job.get("title") or "Untitled role")
                st.write(
                    f"**{job.get('company') or 'Company not specified'}** · "
                    f"{job.get('location') or 'Location not specified'}"
                )
                st.write(
                    f"Current stage: "
                    f"**{STATUS_LABELS.get(current_status, current_status)}**"
                )

                if job.get("url"):
                    st.link_button(
                        "View original listing",
                        job["url"],
                        key=f"application-link-{job_id}",
                    )

                with st.expander("Update application"):
                    with st.form(f"application-{job_id}"):
                        new_status = st.selectbox(
                            "Status",
                            STATUSES,
                            index=(
                                STATUSES.index(current_status)
                                if current_status in STATUSES
                                else 0
                            ),
                            format_func=lambda value: STATUS_LABELS[value],
                        )

                        new_notes = st.text_area(
                            "Notes",
                            value=job.get("application_notes", ""),
                            placeholder=(
                                "Application date, recruiter contact, "
                                "interview notes, or follow-up actions."
                            ),
                            height=120,
                        )

                        update_submitted = st.form_submit_button(
                            "Save changes",
                            type="primary",
                            use_container_width=True,
                        )

                    if update_submitted:
                        try:
                            api_patch(
                                f"/jobs/{job_id}/status",
                                {
                                    "application_status": new_status,
                                    "application_notes": new_notes,
                                },
                            )
                            st.success("Application updated.")
                            st.rerun()
                        except (httpx.HTTPError, ValueError) as exc:
                            show_error("Could not update application", exc)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()
st.caption("My Job Search · Arbeitnow · FastAPI · SQLite")
