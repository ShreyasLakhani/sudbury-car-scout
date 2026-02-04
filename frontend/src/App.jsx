import { useState, useEffect } from 'react'
import { Container, Grid, Card, Text, Badge, Button, Group, Title, LoadingOverlay, ThemeIcon } from '@mantine/core'

function App() {
  const [cars, setCars] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch data from your Python API
    fetch('http://localhost:8000/cars')
      .then((res) => res.json())
      .then((data) => {
        setCars(data)
        setLoading(false)
      })
      .catch((error) => {
        console.error("Error fetching data:", error)
        setLoading(false)
      })
  }, [])

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>Sudbury Car Scout</Title>
          <Text c="dimmed">Automated Daily Tracker • {cars.length} Active Listings</Text>
        </div>
        <Button 
            component="a" 
            href="http://localhost:8000/cars" 
            target="_blank" 
            variant="outline"
        >
            View Raw API
        </Button>
      </Group>

      <div style={{ position: 'relative', minHeight: '200px' }}>
        <LoadingOverlay visible={loading} zIndex={1000} overlayProps={{ radius: "sm", blur: 2 }} />
        
        <Grid>
          {cars.map((car) => (
            <Grid.Col key={car.id} span={{ base: 12, md: 6, lg: 4 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mt="md" mb="xs">
                  <Text fw={500} lineClamp={1} title={car.title}>
                    {car.title}
                  </Text>
                  <Badge color="green" variant="light">
                    {car.price}
                  </Badge>
                </Group>

                <Text size="sm" c="dimmed" mb="md">
                  Mileage: {car.mileage}
                </Text>

                <Button 
                  component="a" 
                  href={car.link} 
                  target="_blank" 
                  fullWidth 
                  mt="md" 
                  radius="md"
                >
                  View on AutoTrader
                </Button>
              </Card>
            </Grid.Col>
          ))}
        </Grid>
      </div>
    </Container>
  )
}

export default App