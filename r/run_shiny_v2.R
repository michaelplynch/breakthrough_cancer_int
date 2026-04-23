library(shiny)
library(jsonlite)
library(SpatialExperiment)
library(ggplot2)
#library(viridisLite)

# ---- CONFIG ----
coords_path <- "../shared/coords.json"
zoom_radius <- 500   # tissue units to show around foot

# ---- LOAD DATA ----
# Replace with your actual SpatialExperiment object
load("../assets/sfe.rdata")
spe<-sfe
getwd()
coords <- spatialCoords(spe)
plot_df <- data.frame(
  x = coords[, 1],
  y = coords[, 2],
  value = colData(spe)$spottype_low  # or gene expression etc
)


## Radial composition
plot_df$cell_type<-as.factor(plot_df$value)
radii <- seq(50, 500, by = 50)  # tissue units

# ---- UI ----
ui <- fluidPage(
  titlePanel("Spatial transcriptomics – live interaction"),
  fluidRow(
    column(7, plotOutput("spatial_plot", height = "800px")),
    column(5, plotOutput("radial_plot", height = "800px"))
  )
)

# ---- SERVER ----
server <- function(input, output, session) {
  
  # Pull coords.json every 100 ms
  foot_coords <- reactiveFileReader(
    intervalMillis = 1500,
    session = session,
    filePath = coords_path,
    readFunc = function(path) {
      tryCatch(fromJSON(path), error = function(e) NULL)
    }
  )
  
  output$spatial_plot <- renderPlot({
    
    t_start <- Sys.time()
    
    # --- Read JSON ---
    t_read <- Sys.time()
    fc <- foot_coords()
    t_read_done <- Sys.time()
    
    if (is.null(fc) || is.null(fc$tissue_x) || is.null(fc$tissue_y)) {
      
      read_ms <- round(as.numeric(difftime(t_read_done, t_read, units = "auto")), 1)
      
      return(
        ggplot(plot_df, aes(x, y)) +
          geom_point(aes(colour = value), size = 0.4, alpha = 0.5) +
          coord_fixed() +
          theme_void() +
          ggtitle(sprintf(
            "Waiting for interaction… | JSON read: %.1f s",
            read_ms
          ))
      )
    }
    
    fx <- fc$tissue_x
    fy <- fc$tissue_y
    
    # --- Subset ---
    t_subset <- Sys.time()
    subset_df <- plot_df[
      plot_df$x >= fx - zoom_radius &
        plot_df$x <= fx + zoom_radius &
        plot_df$y >= fy - zoom_radius &
        plot_df$y <= fy + zoom_radius,
    ]
    t_subset_done <- Sys.time()
    
    # --- Plot ---
    t_plot <- Sys.time()
    
    p <- ggplot(subset_df, aes(x, y)) +
      geom_point(aes(color = value), size = 6) +
      geom_point(
        data = data.frame(x = fx, y = fy),
        aes(x, y),
        color = "red",
        size = 10,
        shape=10
      ) +
      coord_fixed() +
      theme_void()
    
    t_plot_done <- Sys.time()
    
    # --- Timing summary ---
    read_ms   <- round(as.numeric(difftime(t_read_done, t_read, units = "auto")), 3)
    subset_ms <- round(as.numeric(difftime(t_subset_done, t_subset, units = "auto")), 3)
    plot_ms   <- round(as.numeric(difftime(t_plot_done, t_plot, units = "auto")), 3)
    total_ms  <- round(as.numeric(difftime(t_plot_done, t_start, units = "auto")), 3)
    
    p + ggtitle(sprintf(
      "Read: %.3f s | Subset: %.3f s | Plot: %.3f s | Total: %.3f s",
      read_ms, subset_ms, plot_ms, total_ms
    ))
  })
  
  # output$radial_plot <- renderPlot({
  #   ggplot(mtcars, aes(wt, mpg)) + geom_point()
  # })
  # 
  output$radial_plot <- renderPlot({

    fc <- foot_coords()
    if (is.null(fc) || is.null(fc$tissue_x) || is.null(fc$tissue_y)) {
      return(
        ggplot() +
          theme_void() +
          ggtitle("No interaction")
      )
    }

    fx <- fc$tissue_x
    fy <- fc$tissue_y

    # --- distance computation (vectorised & fast)
    dists <- sqrt((plot_df$x - fx)^2 + (plot_df$y - fy)^2)

    # --- build counts by radius
    radial_counts <- lapply(radii, function(r) {
      idx <- dists <= r
      if (!any(idx)) return(NULL)

      as.data.frame(table(plot_df$cell_type[idx]),
                    stringsAsFactors = FALSE) |>
        transform(radius = r)
    })

    radial_counts <- do.call(rbind, radial_counts)
    colnames(radial_counts) <- c("cell_type", "count", "radius")

    # --- plot
    ggplot(radial_counts,
           aes(x = radius, y = count, color = cell_type)) +
      geom_line(linewidth = 1) +
      geom_point(size = 1) +
      theme_minimal() +
      labs(
        title = "Cell-type counts vs distance",
        x = "Radius from interaction point",
        y = "Number of spots"
      )+
      ggtitle(sprintf(
        "Min dist: %.1f | Max radius: %.1f",
        min(dists), max(radii)
      ))

  })
  
}

shinyApp(ui, server)