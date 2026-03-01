CREATE OR REPLACE VIEW v_user_lipstick
AS SELECT "user".email,
    "user".name,
    "user".pw,
    "user".sex,
    "user".year,
    lipstick.hex_code,
    lipstick.color_id,
    lipstick.cname
   FROM "user"
     LEFT JOIN lipstick ON "user".hex_code = lipstick.hex_code;