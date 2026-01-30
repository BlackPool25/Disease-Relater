#_____________________________________________________________#
# Export Contingency Tables from RDS to CSV
# 
# This script reads the contingency table .rds files and exports
# p-value, odds ratio, and count matrices to CSV format for Python processing.
#
# @Author: Data Pipeline
# January 2026
#
# INPUT:
# Data/Data/2.ContingencyTables/*.rds
#
# OUTPUTS:
# Data/Data/2.ContingencyTables/exported/*_year_*_pvalues.csv
# Data/Data/2.ContingencyTables/exported/*_year_*_counts.csv
# Data/Data/2.ContingencyTables/exported/*_year_*_odds_ratios.csv
# Data/Data/2.ContingencyTables/exported/*_age_*_pvalues.csv
# Data/Data/2.ContingencyTables/exported/*_age_*_counts.csv
# Data/Data/2.ContingencyTables/exported/*_age_*_odds_ratios.csv
#_____________________________________________________________#

# Configuration
base_dir <- "Data/Data/2.ContingencyTables"
output_dir <- file.path(base_dir, "exported")

# Create output directory
dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

# Granularity configurations
granularities <- list(
  ICD = list(size = 1080, pattern = "ICD_ContingencyTables"),
  Blocks = list(size = 131, pattern = "Blocks_ContingencyTables"),
  Chronic = list(size = 46, pattern = "Chronic_ContingencyTables")
)

# Stratum configurations
all_years <- seq(2003, 2014, by = 2)  # 6 time periods
all_ages <- seq(1, 8)  # 8 age groups

# Find all RDS files
rds_files <- list.files(base_dir, pattern = "_ContingencyTables_.*\\.rds$", full.names = TRUE)

cat("=" ,rep("=", 69), "\n", sep = "")
cat("CONTINGENCY TABLE EXPORT TO CSV\n")
cat("=" ,rep("=", 69), "\n", sep = "")
cat("Found", length(rds_files), "RDS files to process\n")
cat("Output directory:", output_dir, "\n\n")

process_rds_file <- function(rds_file, gran_config, sex) {
  filename <- basename(rds_file)
  cat("\nProcessing:", filename, "\n")
  cat("  Matrix size:", gran_config$size, "x", gran_config$size, "\n")
  
  tryCatch({
    # Load RDS file
    CTables <- readRDS(rds_file)
    
    cat("  RDS structure: ", paste(dim(CTables), collapse = " x "), "\n")
    
    num_diag <- gran_config$size
    
    # Process YEAR stratifications (years 1-6)
    for(year_idx in 1:6) {
      year_matched <- all_years[year_idx]
      cat("    Processing year", year_matched, "\n")
      
      # Initialize matrices
      P.value <- matrix(NA, num_diag, num_diag)
      OR <- matrix(0, num_diag, num_diag)
      cases <- matrix(0, num_diag, num_diag)
      
      for(i in 1:num_diag){
        for(k in 1:num_diag){
          # Extract data for this disease pair and year
          # CTables is indexed as [disease_i, disease_k, year, age, ]
          data <- CTables[i, k, year_idx, , ]
          
          # Filter data: keep rows where first column > 5
          if(is.matrix(data) && nrow(data) > 0) {
            data <- data[data[, 1] > 5, , drop = FALSE]
            
            if(nrow(data) >= 2 && length(data) > 4){
              cases[i, k] <- sum(data[, 1])
              
              # Perform Mantel-Haenszel test
              test <- NULL
              tryCatch({
                test <- mantelhaen.test(array(as.vector(t(data)), dim = c(2, 2, nrow(data))), correct = TRUE)
                P.value[i, k] <- test$p.value
                OR[i, k] <- as.numeric(test$estimate)
              }, error = function(e) {
                # If MH test fails, use Fisher's exact test on aggregated table
                tryCatch({
                  # Aggregate 2x2xK tables into 2x2
                  a <- sum(data[data[, 1] == 1, 2])  # Both diseases
                  b <- sum(data[data[, 1] == 0, 2])  # Disease 1 only
                  c <- sum(data[data[, 1] == 1, 3])  # Disease 2 only
                  d <- sum(data[data[, 1] == 0, 3])  # Neither
                  
                  if(a + b > 0 && c + d > 0 && a + c > 0 && b + d > 0) {
                    ft <- fisher.test(matrix(c(a, c, b, d), nrow = 2))
                    P.value[i, k] <- ft$p.value
                    if(b > 0 && c > 0) {
                      OR[i, k] <- (a * d) / (b * c)
                    }
                  }
                }, error = function(e2) {
                  # Failed both tests
                })
              })
            }
          }
        }
      }
      
      # Clean up matrices
      OR[is.na(OR)] <- 0
      OR[is.nan(OR)] <- 0
      OR[is.infinite(OR)] <- 0
      
      # Generate output filenames
      base_name <- paste0(gran_config$pattern, "_", sex, "_year_", year_matched, "-", (year_matched + 1))
      
      pvalue_file <- file.path(output_dir, paste0(base_name, "_pvalues.csv"))
      count_file <- file.path(output_dir, paste0(base_name, "_counts.csv"))
      or_file <- file.path(output_dir, paste0(base_name, "_odds_ratios.csv"))
      
      # Write CSV files (no row/column names for compatibility)
      write.table(P.value, pvalue_file, row.names = FALSE, col.names = FALSE, sep = ",")
      write.table(cases, count_file, row.names = FALSE, col.names = FALSE, sep = ",")
      write.table(OR, or_file, row.names = FALSE, col.names = FALSE, sep = ",")
      
      cat("      Exported:", basename(pvalue_file), "\n")
      cat("      Exported:", basename(count_file), "\n")
      cat("      Exported:", basename(or_file), "\n")
    }
    
    # Process AGE stratifications (ages 1-8)
    for(age_idx in 1:8) {
      cat("    Processing age group", age_idx, "\n")
      
      # Initialize matrices
      P.value <- matrix(NA, num_diag, num_diag)
      OR <- matrix(0, num_diag, num_diag)
      cases <- matrix(0, num_diag, num_diag)
      
      for(i in 1:num_diag){
        for(k in 1:num_diag){
          # Extract data for this disease pair and age
          data <- CTables[i, k, , age_idx, ]
          
          # Filter data: keep rows where first column > 5
          if(is.matrix(data) && nrow(data) > 0) {
            data <- data[data[, 1] > 5, , drop = FALSE]
            
            if(nrow(data) >= 2 && length(data) > 4){
              cases[i, k] <- sum(data[, 1])
              
              # Perform Mantel-Haenszel test
              test <- NULL
              tryCatch({
                test <- mantelhaen.test(array(as.vector(t(data)), dim = c(2, 2, nrow(data))), correct = TRUE)
                P.value[i, k] <- test$p.value
                OR[i, k] <- as.numeric(test$estimate)
              }, error = function(e) {
                # If MH test fails, use Fisher's exact test on aggregated table
                tryCatch({
                  a <- sum(data[data[, 1] == 1, 2])
                  b <- sum(data[data[, 1] == 0, 2])
                  c <- sum(data[data[, 1] == 1, 3])
                  d <- sum(data[data[, 1] == 0, 3])
                  
                  if(a + b > 0 && c + d > 0 && a + c > 0 && b + d > 0) {
                    ft <- fisher.test(matrix(c(a, c, b, d), nrow = 2))
                    P.value[i, k] <- ft$p.value
                    if(b > 0 && c > 0) {
                      OR[i, k] <- (a * d) / (b * c)
                    }
                  }
                }, error = function(e2) {
                  # Failed both tests
                })
              })
            }
          }
        }
      }
      
      # Clean up matrices
      OR[is.na(OR)] <- 0
      OR[is.nan(OR)] <- 0
      OR[is.infinite(OR)] <- 0
      
      # Generate output filenames
      base_name <- paste0(gran_config$pattern, "_", sex, "_age_", age_idx)
      
      pvalue_file <- file.path(output_dir, paste0(base_name, "_pvalues.csv"))
      count_file <- file.path(output_dir, paste0(base_name, "_counts.csv"))
      or_file <- file.path(output_dir, paste0(base_name, "_odds_ratios.csv"))
      
      # Write CSV files
      write.table(P.value, pvalue_file, row.names = FALSE, col.names = FALSE, sep = ",")
      write.table(cases, count_file, row.names = FALSE, col.names = FALSE, sep = ",")
      write.table(OR, or_file, row.names = FALSE, col.names = FALSE, sep = ",")
      
      cat("      Exported:", basename(pvalue_file), "\n")
      cat("      Exported:", basename(count_file), "\n")
      cat("      Exported:", basename(or_file), "\n")
    }
    
    cat("  SUCCESS: Exported all stratifications for", filename, "\n")
    return(TRUE)
    
  }, error = function(e) {
    cat("  ERROR:", e$message, "\n")
    return(FALSE)
  })
}

# Process each RDS file
total_success <- 0
total_failed <- 0

for(rds_file in rds_files) {
  filename <- basename(rds_file)
  
  # Determine granularity and sex from filename
  gran_type <- NULL
  sex <- NULL
  
  for(gran_name in names(granularities)) {
    gran_info <- granularities[[gran_name]]
    if(grepl(gran_info$pattern, filename)) {
      gran_type <- gran_name
      break
    }
  }
  
  if(grepl("Male", filename)) {
    sex <- "Male"
  } else if(grepl("Female", filename)) {
    sex <- "Female"
  }
  
  if(!is.null(gran_type) && !is.null(sex)) {
    success <- process_rds_file(rds_file, granularities[[gran_type]], sex)
    if(success) {
      total_success <- total_success + 1
    } else {
      total_failed <- total_failed + 1
    }
  } else {
    cat("  WARNING: Could not determine granularity/sex for", filename, "\n")
    total_failed <- total_failed + 1
  }
}

cat("\n" ,rep("=", 70), "\n", sep = "")
cat("EXPORT COMPLETE\n")
cat("=" ,rep("=", 69), "\n", sep = "")
cat("Files processed successfully:", total_success, "\n")
cat("Files failed:", total_failed, "\n")
cat("Total CSV files exported:", length(list.files(output_dir, pattern = "\\.csv$")), "\n")
cat("=" ,rep("=", 69), "\n", sep = "")
