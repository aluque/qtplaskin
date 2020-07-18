program test_qtplaskin_data_01
  use ZDPlasKin
  implicit none
  double precision            :: time  = 0.0d0, time_end = 3.0d0, dtime = 1.0d0

  call ZDPlasKin_init()
  call ZDPlasKin_set_config(QTPLASKIN_SAVE=.true.)

  call ZDPlasKin_set_density('   X', 1.0d0, ldens_const=.true.)
  call ZDPlasKin_set_density('X(1)', 1.0d0, ldens_const=.true.)
  call ZDPlasKin_set_density('X(2)', 1.0d0, ldens_const=.true.)

  do while(time .lt. time_end)
    call ZDPlasKin_timestep(time,dtime)
    time = time + dtime
  enddo

end program test_qtplaskin_data_01
