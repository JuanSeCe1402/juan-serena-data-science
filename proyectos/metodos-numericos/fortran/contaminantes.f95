program main
    implicit none
    double precision :: yA, yB, t, h, yA_new, yB_new
    integer :: i, n_steps
    double precision, parameter :: t_final = 2.0d0, eps = 1.0d-3
    logical :: crossed = .false.
    integer :: unitgnuplot

    open(unit=10, file='contaminanteA.txt', status='unknown')
    open(unit=11, file='contaminanteB.txt', status='unknown')
    open(newunit=unitgnuplot, file='plot_script.gp', status='replace')

    ! Condiciones iniciales
    yA = 10.0d0
    yB = 7.0d0
    t = 0.0d0
    h = 0.01d0  ! Paso de tiempo más pequeño para mayor precisión
    n_steps = int(t_final / h)

    do i = 1, n_steps
        call rk_step(yA, yB, t, h, yA_new, yB_new)
        write(10, *) t, yA
        write(11, *) t, yB

        ! Comprobación de la igualdad aproximada con tres cifras significativas
        if (.not. crossed .and. abs(yA_new - yB_new) < eps) then
            print *, 'Las concentraciones de A y B son aproximadamente iguales en t=', t + h
            crossed = .true.
        endif

        yA = yA_new
        yB = yB_new
        t = t + h
    end do

    close(10)
    close(11)

    ! Escribir el script de Gnuplot
    write(unitgnuplot,*) "set term png"
    write(unitgnuplot,*) "set output 'Contaminantes.png'"
    write(unitgnuplot,*) "set title 'Gráfico de la función'"
    write(unitgnuplot,*) "set xlabel 'x'"
    write(unitgnuplot,*) "set ylabel 'f(x)'"
    write(unitgnuplot,*) "set grid"
    write(unitgnuplot,*) "set style fill transparent solid 0.5 noborder"
    write(unitgnuplot,*) "plot 'ContaminanteA.txt' with lines, 'ContaminanteB.txt' with lines"
    write(unitgnuplot,*) "unset output"
    close(unitgnuplot)

contains

    subroutine rk_step(yA, yB, t, h, yA_new, yB_new)
        double precision, intent(in) :: yA, yB, t, h
        double precision, intent(out) :: yA_new, yB_new
        double precision :: k1A, k2A, k3A, k4A
        double precision :: k1B, k2B, k3B, k4B

        k1A = h * dQAdt(yA, t)
        k2A = h * dQAdt(yA + 0.5*k1A, t + 0.5*h)
        k3A = h * dQAdt(yA + 0.5*k2A, t + 0.5*h)
        k4A = h * dQAdt(yA + k3A, t + h)

        k1B = h * dQBdt(yB, t)
        k2B = h * dQBdt(yB + 0.5*k1B, t + 0.5*h)
        k3B = h * dQBdt(yB + 0.5*k2B, t + 0.5*h)
        k4B = h * dQBdt(yB + k3B, t + h)

        yA_new = yA + (k1A + 2*k2A + 2*k3A + k4A) / 6.0
        yB_new = yB + (k1B + 2*k2B + 2*k3B + k4B) / 6.0
    end subroutine rk_step

    function dQAdt(QA, t) result(dQA)
        double precision, intent(in) :: QA, t
        double precision :: dQA
        dQA = -(6.0d0/10.0d0) * QA
    end function dQAdt

    function dQBdt(QB, t) result(dQB)
        double precision, intent(in) :: QB, t
        double precision :: dQB
        dQB = 2.0d0 - (6.0d0/10.0d0) * QB
    end function dQBdt

end program main
