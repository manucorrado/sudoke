export default function AdminDashboard() {
  return (
    <main style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Sudoke Admin</h1>
      <p style={{ color: '#666' }}>
        Puzzle operations dashboard. This will include puzzle import, review workflow, scheduling,
        and inventory management.
      </p>
      <nav style={{ marginTop: '2rem' }}>
        <h2>Sections</h2>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          <li style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>
            Puzzle Import &amp; Validation
          </li>
          <li style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>
            Review Workflow
          </li>
          <li style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>
            Schedule Calendar
          </li>
          <li style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>
            Inventory Status
          </li>
          <li style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>Audit Log</li>
        </ul>
      </nav>
    </main>
  );
}
