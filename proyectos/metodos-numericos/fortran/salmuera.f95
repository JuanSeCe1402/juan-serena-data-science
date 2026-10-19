program runge_kutta_salmuera
    implicit none
    integer, parameter :: n = 10000
    double precision, dimension(0:n) :: t, Q
    double precision :: h, k1, k2, k3, k4
    integer :: i

    ! Inicialización de variables
    h = 11.0d0 / n
    t(0) = 0.0d0
    Q(0) = 0.0d0

    ! Método Runge-Kutta de cuarto orden
    do i = 0, n - 1
        t(i+1) = t(i) + h
        k1 = h * f(t(i), Q(i))
        k2 = h * f(t(i) + h / 2.0d0, Q(i) + k1 / 2.0d0)
        k3 = h * f(t(i) + h / 2.0d0, Q(i) + k2 / 2.0d0)
        k4 = h * f(t(i) + h, Q(i) + k3)
        Q(i+1) = Q(i) + (k1 + 2.0d0 * k2 + 2.0d0 * k3 + k4) / 6.0d0
    end do

    ! Imprimir el resultado
    print *, 'La cantidad de sal en el estanque a los 11 segundos es: ', Q(n)

contains
    ! Función para la tasa de cambio de Q
    double precision function f(t, Q)
        double precision, intent(in) :: t, Q
        f = 18.0d0 - 2.0d0 * Q / (100.0d0 + 4.0d0 * t)
    end function f

end program runge_kutta_salmuera
