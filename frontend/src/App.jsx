import { useState, useEffect, useCallback } from 'react'
import {
  Container, Grid, Card, Text, Badge, Button, Group, Title,
  LoadingOverlay, Paper, Modal, TextInput, NumberInput, Alert,
  Select, Pagination, SimpleGrid, Skeleton, Divider,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function StatCard({ label, value }) {
  return (
    <Paper shadow="xs" p="md" radius="md" withBorder>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600}>{label}</Text>
      <Text size="xl" fw={700} mt={4}>{value ?? '—'}</Text>
    </Paper>
  )
}

function App() {
  const [cars, setCars] = useState([])
  const [chartData, setChartData] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const LIMIT = 12

  // Filters
  const [keyword, setKeyword] = useState('')
  const [minPrice, setMinPrice] = useState(0)
  const [maxPrice, setMaxPrice] = useState(0)
  const [sortBy, setSortBy] = useState('newest')

  // Alert modal
  const [opened, { open, close }] = useDisclosure(false)
  const [alertEmail, setAlertEmail] = useState('')
  const [alertPrice, setAlertPrice] = useState(20000)
  const [alertKeyword, setAlertKeyword] = useState('')
  const [alertError, setAlertError] = useState(null)
  const [alertLoading, setAlertLoading] = useState(false)

  const fetchCars = useCallback(() => {
    setLoading(true)
    setError(null)
    const params = new URLSearchParams({
      page,
      limit: LIMIT,
      keyword,
      min_price: minPrice || 0,
      max_price: maxPrice || 0,
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
  }, [page, keyword, minPrice, maxPrice])

  useEffect(() => {
    fetchCars()
  }, [fetchCars])

  useEffect(() => {
    fetch(`${API_URL}/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
  }, [])

  const handleSearch = () => {
    setPage(1)
    fetchCars()
  }

  const handleSetAlert = () => {
    setAlertError(null)
    setAlertLoading(true)
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
        if (!res.ok) return res.json().then((e) => { throw new Error(e.detail || 'Request failed') })
        return res.json()
      })
      .then(() => {
        setAlertEmail('')
        setAlertPrice(20000)
        setAlertKeyword('')
        close()
      })
      .catch((err) => setAlertError(err.message))
      .finally(() => setAlertLoading(false))
  }

  const sortedCars = [...cars].sort((a, b) => {
    if (sortBy === 'price_asc') {
      return (parseInt(a.price.replace(/[$,]/g, ''), 10) || 0) -
             (parseInt(b.price.replace(/[$,]/g, ''), 10) || 0)
    }
    if (sortBy === 'price_desc') {
      return (parseInt(b.price.replace(/[$,]/g, ''), 10) || 0) -
             (parseInt(a.price.replace(/[$,]/g, ''), 10) || 0)
    }
    if (sortBy === 'mileage_asc') {
      return (parseInt(a.mileage.replace(/[km, ]/g, ''), 10) || 0) -
             (parseInt(b.mileage.replace(/[km, ]/g, ''), 10) || 0)
    }
    return 0
  })

  return (
    <Container size="xl" py="xl" style={{ backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      {/* Header */}
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>Sudbury Car Scout AI</Title>
          <Text c="dimmed">Machine Learning Market Analysis • {total} Listings</Text>
        </div>
        <Button onClick={open} variant="gradient" gradient={{ from: 'indigo', to: 'cyan' }}>
          Set Price Alert
        </Button>
      </Group>

      {/* Alert modal */}
      <Modal opened={opened} onClose={close} title="Get Notified on Price Drops">
        {alertError && (
          <Alert color="red" mb="md" onClose={() => setAlertError(null)} withCloseButton>
            {alertError}
          </Alert>
        )}
        <TextInput
          label="Email"
          placeholder="you@example.com"
          value={alertEmail}
          onChange={(e) => setAlertEmail(e.target.value)}
          mb="md"
        />
        <TextInput
          label="Car Model"
          placeholder="e.g. Civic"
          value={alertKeyword}
          onChange={(e) => setAlertKeyword(e.target.value)}
          mb="md"
        />
        <NumberInput
          label="Notify me below:"
          value={alertPrice}
          onChange={setAlertPrice}
          prefix="$"
          min={500}
          max={500000}
          mb="lg"
        />
        <Button
          onClick={handleSetAlert}
          fullWidth
          loading={alertLoading}
          disabled={!alertEmail || !alertKeyword}
        >
          Activate Alert
        </Button>
      </Modal>

      {/* Stats bar */}
      {stats && (
        <SimpleGrid cols={{ base: 2, sm: 4 }} mb="xl">
          <StatCard label="Total Listings" value={stats.total_listings} />
          <StatCard
            label="Avg Price"
            value={stats.avg_price != null ? `$${stats.avg_price.toLocaleString()}` : null}
          />
          <StatCard
            label="Median Price"
            value={stats.median_price != null ? `$${stats.median_price.toLocaleString()}` : null}
          />
          <StatCard
            label="Avg Mileage"
            value={stats.avg_mileage != null ? `${Math.round(stats.avg_mileage).toLocaleString()} km` : null}
          />
        </SimpleGrid>
      )}

      {/* AI Chart */}
      <Paper shadow="sm" p="md" mb="xl" radius="md" withBorder>
        <Title order={4} mb="md">AI Valuation Curve</Title>
        <div style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="mileageNum" name="Mileage" unit=" km" domain={['auto', 'auto']} />
              <YAxis type="number" dataKey="priceNum" name="Price" unit="$" domain={['auto', 'auto']} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Cars" data={chartData} fill="#228be6" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </Paper>

      {/* Filters */}
      <Paper shadow="xs" p="md" mb="lg" radius="md" withBorder>
        <Group align="flex-end" wrap="wrap">
          <TextInput
            label="Search by model"
            placeholder="e.g. Honda Civic"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            style={{ flex: 1, minWidth: 160 }}
          />
          <NumberInput
            label="Min Price ($)"
            value={minPrice || ''}
            onChange={(v) => setMinPrice(Number(v) || 0)}
            min={0}
            style={{ width: 130 }}
          />
          <NumberInput
            label="Max Price ($)"
            value={maxPrice || ''}
            onChange={(v) => setMaxPrice(Number(v) || 0)}
            min={0}
            style={{ width: 130 }}
          />
          <Select
            label="Sort by"
            value={sortBy}
            onChange={setSortBy}
            data={[
              { value: 'newest', label: 'Newest' },
              { value: 'price_asc', label: 'Price: Low to High' },
              { value: 'price_desc', label: 'Price: High to Low' },
              { value: 'mileage_asc', label: 'Mileage: Low to High' },
            ]}
            style={{ width: 180 }}
          />
          <Button onClick={handleSearch}>Search</Button>
        </Group>
      </Paper>

      {/* Error state */}
      {error && (
        <Alert color="red" mb="lg" title="Failed to load listings" withCloseButton onClose={() => setError(null)}>
          {error} — <Button variant="subtle" size="xs" onClick={fetchCars}>Retry</Button>
        </Alert>
      )}

      {/* Car grid */}
      <div style={{ position: 'relative' }}>
        <LoadingOverlay visible={loading} />
        {loading ? (
          <Grid>
            {Array.from({ length: 6 }).map((_, i) => (
              <Grid.Col key={i} span={{ base: 12, md: 6, lg: 4 }}>
                <Skeleton height={180} radius="md" />
              </Grid.Col>
            ))}
          </Grid>
        ) : (
          <Grid align="stretch">
            {sortedCars.map((car) => (
              <Grid.Col key={car.id} span={{ base: 12, md: 6, lg: 4 }}>
                <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
                  <Group justify="space-between" mt="md" mb="xs">
                    <Badge color="blue" variant="light">{car.price}</Badge>
                    {car.deal_rating && car.deal_rating !== 'N/A' && (
                      <Badge color={car.deal_color} variant="filled">{car.deal_rating}</Badge>
                    )}
                  </Group>
                  <Text fw={700} size="lg" lineClamp={2} title={car.title} style={{ minHeight: '50px' }}>
                    {car.title}
                  </Text>
                  <Text size="sm" c="dimmed" mt="sm">
                    Mileage: <b>{car.mileage}</b>
                  </Text>
                  <Button
                    component="a"
                    href={car.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    fullWidth
                    mt="md"
                    radius="md"
                    variant="filled"
                    color="blue"
                  >
                    View Listing
                  </Button>
                </Card>
              </Grid.Col>
            ))}
          </Grid>
        )}
      </div>

      {/* Pagination */}
      {total > LIMIT && (
        <>
          <Divider my="xl" />
          <Group justify="center">
            <Pagination
              value={page}
              onChange={setPage}
              total={Math.ceil(total / LIMIT)}
            />
          </Group>
        </>
      )}
    </Container>
  )
}

export default App
