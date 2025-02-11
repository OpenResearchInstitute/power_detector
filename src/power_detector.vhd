------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------
--  _______                             ________                                            ______
--  __  __ \________ _____ _______      ___  __ \_____ _____________ ______ ___________________  /_
--  _  / / /___  __ \_  _ \__  __ \     __  /_/ /_  _ \__  ___/_  _ \_  __ `/__  ___/_  ___/__  __ \
--  / /_/ / __  /_/ //  __/_  / / /     _  _, _/ /  __/_(__  ) /  __// /_/ / _  /    / /__  _  / / /
--  \____/  _  .___/ \___/ /_/ /_/      /_/ |_|  \___/ /____/  \___/ \__,_/  /_/     \___/  /_/ /_/
--          /_/
--                   ________                _____ _____ _____         _____
--                   ____  _/_______ __________  /____(_)__  /_____  ____  /______
--                    __  /  __  __ \__  ___/_  __/__  / _  __/_  / / /_  __/_  _ \
--                   __/ /   _  / / /_(__  ) / /_  _  /  / /_  / /_/ / / /_  /  __/
--                   /___/   /_/ /_/ /____/  \__/  /_/   \__/  \__,_/  \__/  \___/
--
------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------
-- Copyright
------------------------------------------------------------------------------------------------------
--
-- Copyright 2024 by M. Wishek <matthew@wishek.com>
--
------------------------------------------------------------------------------------------------------
-- License
------------------------------------------------------------------------------------------------------
--
-- This source describes Open Hardware and is licensed under the CERN-OHL-W v2.
--
-- You may redistribute and modify this source and make products using it under
-- the terms of the CERN-OHL-W v2 (https://ohwr.org/cern_ohl_w_v2.txt).
--
-- This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY, INCLUDING
-- OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A PARTICULAR PURPOSE.
-- Please see the CERN-OHL-W v2 for applicable conditions.
--
-- Source location: TBD
--
-- As per CERN-OHL-W v2 section 4.1, should You produce hardware based on this
-- source, You must maintain the Source Location visible on the external case of
-- the products you make using this source.
--
------------------------------------------------------------------------------------------------------
-- Block name and description
------------------------------------------------------------------------------------------------------
--
-- This block implements a power detector.
--
-- Documentation location: TBD
--
------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------
-- ╦  ┬┌┐ ┬─┐┌─┐┬─┐┬┌─┐┌─┐
-- ║  │├┴┐├┬┘├─┤├┬┘│├┤ └─┐
-- ╩═╝┴└─┘┴└─┴ ┴┴└─┴└─┘└─┘
------------------------------------------------------------------------------------------------------
-- Libraries

LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE ieee.numeric_std.ALL;


------------------------------------------------------------------------------------------------------
-- ╔═╗┌┐┌┌┬┐┬┌┬┐┬ ┬
-- ║╣ │││ │ │ │ └┬┘
-- ╚═╝┘└┘ ┴ ┴ ┴  ┴ 
------------------------------------------------------------------------------------------------------
-- Entity

ENTITY power_detector IS 
	GENERIC (
		DATA_W 			: NATURAL := 12;
		ALPHA_W 		: NATURAL := 18;
		IQ_MOD 			: BOOLEAN := False;
		I_USED 			: BOOLEAN := True;
		Q_USED 			: BOOLEAN := False;
		EMA_CASCADE		: BOOLEAN := True
	);
	PORT (
		clk				: IN  std_logic;
		init			: IN  std_logic;

		alpha1			: IN  std_logic_vector(ALPHA_W -1 DOWNTO 0);
		alpha2			: IN  std_logic_vector(ALPHA_W -1 DOWNTO 0);

		data_I			: IN  std_logic_vector(DATA_W -1 DOWNTO 0);
		data_Q			: IN  std_logic_vector(DATA_W -1 DOWNTO 0);
		data_ena		: IN  std_logic;

		power_squared	: OUT std_logic_vector(2*DATA_W -2 DOWNTO 0)
	);
END ENTITY power_detector;

------------------------------------------------------------------------------------------------------
-- ╔═╗┬─┐┌─┐┬ ┬┬┌┬┐┌─┐┌─┐┌┬┐┬ ┬┬─┐┌─┐
-- ╠═╣├┬┘│  ├─┤│ │ ├┤ │   │ │ │├┬┘├┤ 
-- ╩ ╩┴└─└─┘┴ ┴┴ ┴ └─┘└─┘ ┴ └─┘┴└─└─┘
------------------------------------------------------------------------------------------------------
-- Architecture

ARCHITECTURE rtl OF power_detector IS 

	SIGNAL di_sq	: unsigned(2*DATA_W -2 DOWNTO 0);
	SIGNAL dq_sq	: unsigned(2*DATA_W -2 DOWNTO 0);
	SIGNAL dsum 	: unsigned(2*DATA_W -2 DOWNTO 0);
	SIGNAL dsum_e1  : std_logic;
	SIGNAL dsum_e2  : std_logic;
	SIGNAL ema_1	: std_logic_vector(2*DATA_W -2 DOWNTO 0);
	SIGNAL ema_1_ena: std_logic;
	SIGNAL ema_2 	: std_logic_vector(2*DATA_W -2 DOWNTO 0);
	SIGNAL ema_2_ena: std_logic;

BEGIN 

	input_proc : PROCESS (clk)
	BEGIN
		IF clk'EVENT AND clk = '1' THEN
			IF init = '1' THEN
				di_sq 	<= (OTHERS => '0');
				dq_sq 	<= (OTHERS => '0');
				dsum  	<= (OTHERS => '0');
				dsum_e1 <= '0';
				dsum_e2 <= '0';
			ELSE

				dsum_e1 <= data_ena;
				dsum_e2 <= dsum_e1;

				di_sq <= resize(unsigned(signed(data_I) * signed(data_I)), 2*DATA_W -1);
				dq_sq <= resize(unsigned(signed(data_Q) * signed(data_Q)), 2*DATA_W -1);

				IF IQ_MOD THEN

					dsum <= resize(shift_right(di_sq + dq_sq, 0), 2*DATA_W -1);

				ELSIF I_USED THEN

					dsum <= resize(shift_right(di_sq, 0), 2*DATA_W -1);

				ELSE -- Q_USED

					dsum <= resize(shift_right(dq_sq, 0), 2*DATA_W -1);

				END IF;

			END IF;
		END IF;
	END PROCESS input_proc;

	u_ema_1 : ENTITY work.lowpass_ema(rtl)
	GENERIC MAP (
		DATA_W 	=> 2*DATA_W -1,
		ALPHA_W => ALPHA_W
	)
	PORT MAP (
		clk				=> clk,
		init			=> init,

		alpha 			=> alpha1,

		data 			=> std_logic_vector(dsum),
		data_ena 		=> dsum_e2,

		average 		=> ema_1,
		average_ena 	=> ema_1_ena
	);

	ema_2_cascade: IF EMA_CASCADE GENERATE
		u_ema_2 : ENTITY work.lowpass_ema(rtl)
		GENERIC MAP (
			DATA_W 	=> 2*DATA_W -1,
			ALPHA_W => ALPHA_W
		)
		PORT MAP (
			clk				=> clk,
			init			=> init,
	
			alpha 			=> alpha2,
	
			data 			=> ema_1,
			data_ena 		=> ema_1_ena,
	
			average 		=> ema_2,
			average_ena		=> ema_2_ena
		);
	END GENERATE;

	power_squared <= ema_2 WHEN EMA_CASCADE ELSE ema_1;

END ARCHITECTURE rtl;



