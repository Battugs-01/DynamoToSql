-- Fix kyc_infos table to allow NULL values
-- Run this on your PostgreSQL database

-- Make fail_reason nullable
ALTER TABLE kyc_infos 
ALTER COLUMN fail_reason DROP NOT NULL;

-- Make kyc_passed nullable
ALTER TABLE kyc_infos 
ALTER COLUMN kyc_passed DROP NOT NULL;

-- Make kyc_status nullable
ALTER TABLE kyc_infos 
ALTER COLUMN kyc_status DROP NOT NULL;

-- Verify changes
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'kyc_infos' 
  AND column_name IN ('fail_reason', 'kyc_passed', 'kyc_status')
ORDER BY column_name;
