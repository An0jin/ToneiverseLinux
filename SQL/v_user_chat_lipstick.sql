-- public.v_user_chat_lipstick source

CREATE OR REPLACE VIEW v_user_chat_lipstick
AS SELECT chat_id,
    name,
    msg,
    chat.color_id
   FROM v_user_lipstick
     JOIN chat ON v_user_lipstick.email = chat.email
  ORDER BY chat."time";