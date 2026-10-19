program epidemia
  implicit none
  ! Declaración e inicialización de variables
  double precision, parameter :: m = 1000.0
  double precision :: k, x_0, t, dt, x, x_new
  integer :: i, n

  k = 1.0d0 / (5 * m) * log(9.0d0 / 4.0d0)
  x_0 = m / 10.0d0
  t = 0.0d0
  n = 1000
  dt = 10.0d0 / n
  x = x_0

  ! Runge Kutta
  do i = 1, n
     call runge_kutta(t, x, dt, k, m, x_new)
     x = x_new
     t = t + dt
  end do

  print *, 'El numero de infectados despues de 10 dias es ', x

  ! Resetear el tiempo y el número de infectados para el otro calculo
  t = 0.0d0
  x = x_0

  ! Encontrar el tiempo cuando la mitaad de la población esta infectada
  do while (x < m / 2.0d0)
     call runge_kutta(t, x, dt, k, m, x_new)
     x = x_new
     t = t + dt
  end do

  print *, 'El tiempo para cuando la mitad de población se infecta es ', t, ' dias.'

contains
  subroutine runge_kutta(t, x, dt, k, m, x_new)
    implicit none
    double precision, intent(in) :: t, x, dt, k, m
    double precision, intent(out) :: x_new
    double precision :: k1, k2, k3, k4

    ! Calculo de los valores de k
    k1 = dt * dxdt(t, x, k, m)
    k2 = dt * dxdt(t + dt / 2.0d0, x + k1 / 2.0d0, k, m)
    k3 = dt * dxdt(t + dt / 2.0d0, x + k2 / 2.0d0, k, m)
    k4 = dt * dxdt(t + dt, x + k3, k, m)

    ! Calculo de x_new
    x_new = x + (k1 + 2.0d0 * k2 + 2.0d0 * k3 + k4) / 6.0d0
  end subroutine runge_kutta

  function dxdt(t, x, k, m) result(derivative)
    double precision, intent(in) :: t, x, k, m
    double precision :: derivative

    ! Derivada x respecto a t
    derivative = k * x * (m - x)
  end function dxdt

end program epidemia
