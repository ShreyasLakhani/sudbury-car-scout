import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Container, Grid, Card, Text, Badge, Button, Group, Title,
  LoadingOverlay, Paper, Modal, TextInput, NumberInput, Alert,
  Select, Pagination, SimpleGrid, Skeleton, Divider, Box,
} from '@mantine/core'
import { useDisclosure, useDebouncedValue } from '@mantine/hooks'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const LIMIT = 12

// ─── Stat Card Component ─────────────────────────────────────────────────────

function StatCard({ label, value, delay = 0 }) {
  return (
    <Paper
      className="stat-card"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value ?? '—'}</div>
    </Paper>
  )
}

// ─── Deal Badge Component ────────────────────────────────────────────────────

function DealBadge({ rating, color }) {
  if (!rating || rating === 'N/A') return null

  const classMap = {
    'GREAT DEAL': 'deal-badge-great',
    'GOOD DEAL': 'deal-badge-good',
    'FAIR PRICE': 'deal-badge-fair',
    'OVERPRICED': 'deal-badge-overpriced',
  }

  return (
    <Badge className={classMap[rating] || 'deal-badge-fair'} size="sm">
      {rating}
    </Badge>
  )
}

// ─── Skeleton Card ───────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <Card className="skeleton-card" padding="lg" h={220}>
      <Group justify="space-between" mb="xs">
        <Skeleton height={24} width={80} className="skeleton-shimmer" radius="xl" />
        <Skeleton height={24} width={100} className="skeleton-shimmer" radius="xl" />
      </Group>
      <Skeleton height={20} mt="md" className="skeleton-shimmer" />
      <Skeleton height={20} mt="xs" width="70%" className="skeleton-shimmer" />
      <Skeleton height={14} mt="md" width="40%" className="skeleton-shimmer" />
      <Skeleton height={36} mt="lg" className="skeleton-shimmer" radius="md" />
    </Card>
  )
}

// ─── Empty State ─────────────────────────────────────────────────────────────

function EmptyState({ keyword }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">🔍</div>
      <Title order={3} c="dimmed" mb="xs">No listings found</Title>
      <Text c="dimmed" size="sm">
        {keyword
          ? `No cars match "${keyword}". Try a different search.`
          : 'No car listings available at the moment.'}
      </Text>
    </div>
  )
}

// ─── Main App ────────────────────────────────────────────────────────────────

function App() {
  // Data state
  const [cars, setCars] = useState([])
  const [chartData, setChartData] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)

  // Filters
  const [keyword, setKeyword] = useState('')
  const [minPrice, setMinPrice] = useState(0)
  const [maxPrice, setMaxPrice] = useState(0)
  const [sortBy, setSortBy] = useState('newest')

  // Debounce keyword to prevent lag on every keystroke
  const [debouncedKeyword] = useDebouncedValue(keyword, 300)

  // Alert modal
  const [opened, { open, close }] = useDisclosure(false)
  const [alertEmail, setAlertEmail] = useState('')
  const [alertPrice, setAlertPrice] = useState(20000)
  const [alertKeyword, setAlertKeyword] = useState('')
  const [alertError, setAlertError] = useState(null)
  const [alertLoading, setAlertLoading] = useState(false)
  const [alertSuccess, setAlertSuccess] = useState(false)

  // ─── Fetch Cars ──────────────────────────────────────────────────────────

  const fetchCars = useCallback(() => {
    setLoading(true)
    setError(null)

    const params = new URLSearchParams({
      page: String(page),
      limit: String(LIMIT),
      keyword: debouncedKeyword,
      min_price: String(minPrice || 0),
      max_price: String(maxPrice || 0),
    })

    fetch(`${API_URL}/cars?${params}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Server error: ${res.status}`)
        return res.json()
      })
      .then((data) => {
        const list = data.cars ?? []
        setCars(list)
        setTotal(data.total ?? 0)

        // Prepare chart data
        const validForChart = list
          .map((car) => ({
            ...car,
            priceNum: parseInt(car.price.replace(/[$,]/g, ''), 10) || null,
            mileageNum: parseInt(car.mileage.replace(/[km, ]/g, ''), 10) || null,
          }))
          .filter((car) => car.priceNum > 0 && car.mileageNum > 0)

        setChartData(validForChart)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [page, debouncedKeyword, minPrice, maxPrice])

  useEffect(() => {
    fetchCars()
  }, [fetchCars])

  // ─── Fetch Stats ─────────────────────────────────────────────────────────

  useEffect(() => {
    fetch(`${API_URL}/stats`)
      .then((r) => {
        if (!r.ok) throw new Error('Stats unavailable')
        return r.json()
      })
      .then(setStats)
      .catch(() => {})
  }, [])

  // ─── Search Handler ──────────────────────────────────────────────────────

  const handleSearch = useCallback(() => {
    setPage(1)
    // fetchCars will trigger via useEffect when page changes
  }, [])

  // ─── Sort Cars (client-side within page) ─────────────────────────────────

  const sortedCars = useMemo(() => {
    const sorted = [...cars]
    if (sortBy === 'price_asc') {
      sorted.sort(
        (a, b) =>
          (parseInt(a.price.replace(/[$,]/g, ''), 10) || 0) -
          (parseInt(b.price.replace(/[$,]/g, ''), 10) || 0)
      )
    } else if (sortBy === 'price_desc') {
      sorted.sort(
        (a, b) =>
          (parseInt(b.price.replace(/[$,]/g, ''), 10) || 0) -
          (parseInt(a.price.replace(/[$,]/g, ''), 10) || 0)
      )
    } else if (sortBy === 'mileage_asc') {
      sorted.sort(
        (a, b) =>
          (parseInt(a.mileage.replace(/[km, ]/g, ''), 10) || 0) -
          (parseInt(b.mileage.replace(/[km, ]/g, ''), 10) || 0)
      )
    }
    return sorted
  }, [cars, sortBy])

  // ─── Alert Handler ───────────────────────────────────────────────────────

  const handleSetAlert = useCallback(() => {
    setAlertError(null)
    setAlertLoading(true)
    setAlertSuccess(false)

    fetch(`${API_URL}/alert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: alertEmail,
        target_price: alertPrice,
        keyword: alertKeyword,
      }),
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((e) => {
            throw new Error(e.detail || 'Request failed')
          })
        }
        return res.json()
      })
      .then(() => {
        setAlertSuccess(true)
        setTimeout(() => {
          setAlertEmail('')
          setAlertPrice(20000)
          setAlertKeyword('')
          setAlertSuccess(false)
          close()
        }, 1500)
      })
      .catch((err) => setAlertError(err.message))
      .finally(() => setAlertLoading(false))
  }, [alertEmail, alertPrice, alertKeyword, close])

  // ─── Page Change Handler ─────────────────────────────────────────────────

  const handlePageChange = useCallback((newPage) => {
    setPage(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  // ─── Render ──────────────────────────────────────────────────────────────

  const totalPages = Math.ceil(total / LIMIT)

  return (
    <div className="app-container">
      <div className="app-content">
        {/* ═══ Hero Header ═══ */}
        <div className="hero-header">
          <Container size="xl">
            <Group justify="space-between" align="center">
              <div>
                <h1 className="hero-title">Sudbury Car Scout AI</h1>
                <div className="hero-subtitle">
                  Machine Learning Market Analysis • {total.toLocaleString()} Listings
                </div>
              </div>
              <Button
                className="alert-btn"
                onClick={open}
                size="md"
              >
                🔔 Set Price Alert
              </Button>
            </Group>
          </Container>
        </div>

        <Container size="xl" pb="xl">
          {/* ═══ Stats Bar ═══ */}
          {stats && (
            <SimpleGrid
              cols={{ base: 2, sm: 4 }}
              mb="xl"
              className="stats-grid"
            >
              <StatCard
                label="Total Listings"
                value={stats.total_listings?.toLocaleString()}
                delay={0}
              />
              <StatCard
                label="Avg Price"
                value={stats.avg_price != null ? `$${Math.round(stats.avg_price).toLocaleString()}` : null}
                delay={100}
              />
              <StatCard
                label="Median Price"
                value={stats.median_price != null ? `$${Math.round(stats.median_price).toLocaleString()}` : null}
                delay={200}
              />
              <StatCard
                label="Avg Mileage"
                value={stats.avg_mileage != null ? `${Math.round(stats.avg_mileage).toLocaleString()} km` : null}
                delay={300}
              />
            </SimpleGrid>
          )}

          {/* ═══ Filter Bar ═══ */}
          <Paper className="filter-bar" mb="xl" id="filter-bar">
            <Group align="flex-end" wrap="wrap" gap="md">
              <TextInput
                label="Search by model"
                placeholder="e.g. Honda Civic"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                style={{ flex: 1, minWidth: 180 }}
                styles={{
                  input: {
                    backgroundColor: 'rgba(255,255,255,0.04)',
                    borderColor: 'rgba(255,255,255,0.08)',
                    color: 'var(--text-primary)',
                  },
                  label: { color: 'var(--text-secondary)', fontWeight: 500 },
                }}
              />
              <NumberInput
                label="Min Price ($)"
                value={minPrice || ''}
                onChange={(v) => setMinPrice(Number(v) || 0)}
                min={0}
                step={1000}
                style={{ width: 140 }}
                styles={{
                  input: {
                    backgroundColor: 'rgba(255,255,255,0.04)',
                    borderColor: 'rgba(255,255,255,0.08)',
                    color: 'var(--text-primary)',
                  },
                  label: { color: 'var(--text-secondary)', fontWeight: 500 },
                }}
              />
              <NumberInput
                label="Max Price ($)"
                value={maxPrice || ''}
                onChange={(v) => setMaxPrice(Number(v) || 0)}
                min={0}
                step={1000}
                style={{ width: 140 }}
                styles={{
                  input: {
                    backgroundColor: 'rgba(255,255,255,0.04)',
                    borderColor: 'rgba(255,255,255,0.08)',
                    color: 'var(--text-primary)',
                  },
                  label: { color: 'var(--text-secondary)', fontWeight: 500 },
                }}
              />
              <Select
                label="Sort by"
                value={sortBy}
                onChange={setSortBy}
                data={[
                  { value: 'newest', label: 'Newest First' },
                  { value: 'price_asc', label: 'Price: Low → High' },
                  { value: 'price_desc', label: 'Price: High → Low' },
                  { value: 'mileage_asc', label: 'Mileage: Low → High' },
                ]}
                style={{ width: 190 }}
                styles={{
                  input: {
                    backgroundColor: 'rgba(255,255,255,0.04)',
                    borderColor: 'rgba(255,255,255,0.08)',
                    color: 'var(--text-primary)',
                  },
                  label: { color: 'var(--text-secondary)', fontWeight: 500 },
                }}
              />
              <Button className="search-btn" onClick={handleSearch}>
                Search
              </Button>
            </Group>
          </Paper>

          {/* ═══ AI Chart ═══ */}
          {chartData.length > 0 && (
            <Paper className="chart-panel" shadow="sm" p="lg" mb="xl" withBorder>
              <Title order={4} mb="md" className="chart-title">
                📈 AI Valuation Curve
              </Title>
              <div style={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(255,255,255,0.06)"
                    />
                    <XAxis
                      type="number"
                      dataKey="mileageNum"
                      name="Mileage"
                      unit=" km"
                      domain={['auto', 'auto']}
                      stroke="var(--text-muted)"
                      tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                    />
                    <YAxis
                      type="number"
                      dataKey="priceNum"
                      name="Price"
                      unit="$"
                      domain={['auto', 'auto']}
                      stroke="var(--text-muted)"
                      tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                    />
                    <Tooltip
                      cursor={{ strokeDasharray: '3 3', stroke: 'var(--accent-indigo)' }}
                      contentStyle={{
                        backgroundColor: 'var(--bg-secondary)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--text-primary)',
                      }}
                    />
                    <Scatter
                      name="Cars"
                      data={chartData}
                      fill="var(--accent-indigo)"
                      fillOpacity={0.7}
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </Paper>
          )}

          {/* ═══ Error State ═══ */}
          {error && (
            <Alert
              className="error-alert"
              color="red"
              mb="lg"
              title="Failed to load listings"
              withCloseButton
              onClose={() => setError(null)}
            >
              {error}
              <Button
                variant="subtle"
                color="red"
                size="xs"
                ml="sm"
                onClick={fetchCars}
              >
                Retry
              </Button>
            </Alert>
          )}

          {/* ═══ Car Grid ═══ */}
          <Box style={{ position: 'relative', minHeight: 200 }}>
            {loading ? (
              <Grid>
                {Array.from({ length: 6 }).map((_, i) => (
                  <Grid.Col key={i} span={{ base: 12, md: 6, lg: 4 }}>
                    <SkeletonCard />
                  </Grid.Col>
                ))}
              </Grid>
            ) : sortedCars.length === 0 ? (
              <EmptyState keyword={keyword} />
            ) : (
              <Grid align="stretch">
                {sortedCars.map((car) => (
                  <Grid.Col key={car.id} span={{ base: 12, md: 6, lg: 4 }}>
                    <Card
                      className="car-card"
                      shadow="sm"
                      padding="lg"
                      h="100%"
                    >
                      <Group justify="space-between" mt="xs" mb="xs">
                        <Badge className="price-badge" size="lg">
                          {car.price}
                        </Badge>
                        <DealBadge rating={car.deal_rating} color={car.deal_color} />
                      </Group>

                      <Text
                        fw={700}
                        size="lg"
                        lineClamp={2}
                        title={car.title}
                        className="car-title"
                      >
                        {car.title}
                      </Text>

                      <Text className="car-mileage" mt="sm">
                        🏎️ {car.mileage}
                      </Text>

                      <Button
                        component="a"
                        href={car.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        fullWidth
                        mt="auto"
                        className="view-btn"
                      >
                        View Listing →
                      </Button>
                    </Card>
                  </Grid.Col>
                ))}
              </Grid>
            )}
          </Box>

          {/* ═══ Pagination ═══ */}
          {totalPages > 1 && (
            <div className="pagination-wrapper">
              <Divider my="xl" color="rgba(255,255,255,0.06)" />
              <Group justify="center">
                <Pagination
                  value={page}
                  onChange={handlePageChange}
                  total={totalPages}
                  color="indigo"
                  size="md"
                  radius="md"
                  withEdges
                />
              </Group>
            </div>
          )}
        </Container>

        {/* ═══ Alert Modal ═══ */}
        <Modal
          opened={opened}
          onClose={() => {
            close()
            setAlertError(null)
            setAlertSuccess(false)
          }}
          title={
            <Text fw={700} size="lg">
              🔔 Get Notified on Price Drops
            </Text>
          }
          centered
          radius="lg"
          overlayProps={{ backgroundOpacity: 0.6, blur: 4 }}
          styles={{
            content: {
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
            },
            header: { backgroundColor: 'var(--bg-secondary)' },
          }}
        >
          {alertSuccess && (
            <Alert color="green" mb="md" radius="md">
              ✅ Alert created successfully! You&apos;ll be notified.
            </Alert>
          )}

          {alertError && (
            <Alert
              className="modal-alert-error"
              color="red"
              mb="md"
              onClose={() => setAlertError(null)}
              withCloseButton
              radius="md"
            >
              {alertError}
            </Alert>
          )}

          <TextInput
            label="Email"
            placeholder="you@example.com"
            value={alertEmail}
            onChange={(e) => setAlertEmail(e.target.value)}
            mb="md"
            required
            styles={{
              input: {
                backgroundColor: 'rgba(255,255,255,0.04)',
                borderColor: 'rgba(255,255,255,0.08)',
                color: 'var(--text-primary)',
              },
              label: { color: 'var(--text-secondary)' },
            }}
          />

          <TextInput
            label="Car Model"
            placeholder="e.g. Civic, Corolla"
            value={alertKeyword}
            onChange={(e) => setAlertKeyword(e.target.value)}
            mb="md"
            required
            maxLength={100}
            styles={{
              input: {
                backgroundColor: 'rgba(255,255,255,0.04)',
                borderColor: 'rgba(255,255,255,0.08)',
                color: 'var(--text-primary)',
              },
              label: { color: 'var(--text-secondary)' },
            }}
          />

          <NumberInput
            label="Notify me below:"
            value={alertPrice}
            onChange={setAlertPrice}
            prefix="$"
            min={500}
            max={500000}
            step={500}
            mb="lg"
            styles={{
              input: {
                backgroundColor: 'rgba(255,255,255,0.04)',
                borderColor: 'rgba(255,255,255,0.08)',
                color: 'var(--text-primary)',
              },
              label: { color: 'var(--text-secondary)' },
            }}
          />

          <Button
            className="alert-btn"
            onClick={handleSetAlert}
            fullWidth
            loading={alertLoading}
            disabled={!alertEmail || !alertKeyword || alertSuccess}
          >
            {alertSuccess ? '✓ Alert Created' : 'Activate Alert'}
          </Button>
        </Modal>
      </div>
    </div>
  )
}

export default App