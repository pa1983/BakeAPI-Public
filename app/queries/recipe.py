from sqlalchemy  import text

recipeCostAnalysisQuery = text("""
      WITH RECURSIVE FullRecipeBreakdown (
                                          parent_recipe_id,
                                          recipe_id,
                                          scaling_factor,
                                          recursion_level
          ) AS (
          -- 1. ANCHOR: The starting recipe.
          SELECT
              CAST(NULL AS SIGNED) AS parent_recipe_id, -- The top-level has a NULL parent.
              recipe_id,
              CAST(1.0 AS DECIMAL(20, 10)) AS scaling_factor,
              0 AS recursion_level
          FROM recipe
          WHERE recipe_id = :top_recipe_id and organisation_id = :organisation_id

          UNION ALL

          -- 2. RECURSIVE: Traverse down the recipe hierarchy.
          SELECT
              rsr.parent_recipe_id,
              rsr.sub_recipe_id,
              (frb.scaling_factor * (rsr.quantity * uom_needed.conversion_factor) / (sub_recipe.recipe_quantity * uom_produced.conversion_factor)) AS scaling_factor,
              frb.recursion_level + 1
          FROM
              FullRecipeBreakdown AS frb
                  INNER JOIN recipe_sub_recipe AS rsr ON frb.recipe_id = rsr.parent_recipe_id
                  INNER JOIN recipe AS sub_recipe ON rsr.sub_recipe_id = sub_recipe.recipe_id
                  INNER JOIN unit_of_measure AS uom_needed ON rsr.uom_id = uom_needed.uom_id
                  INNER JOIN unit_of_measure AS uom_produced ON sub_recipe.recipe_uom_id = uom_produced.uom_id
          WHERE
              sub_recipe.recipe_quantity IS NOT NULL AND sub_recipe.recipe_quantity > 0
            AND uom_produced.conversion_factor IS NOT NULL AND uom_produced.conversion_factor > 0
            AND uom_needed.type = uom_produced.type
      ),
                     CombinedCosts AS (
                         -- This CTE gathers and standardises both labour and ingredient costs.  To facilitate this, query fields have been normalised to allow for union of both (and machinery/energy later once implements) 

                         -- Part 1: Labour Costs
                         SELECT
                             'Labour' AS cost_type,
                             frb.recipe_id,
                             r.recipe_name,
                             frb.parent_recipe_id,
                             l.id AS item_id,
                             l.name AS item_name,
                             lc.name AS item_category,
                             top_level_recipe.recipe_id AS top_level_recipe_id,
                             top_level_recipe.recipe_name AS top_level_recipe_name,
                             top_level_recipe.recipe_quantity AS top_level_batch_quantity,
                             top_level_uom.abbreviation AS top_level_uom,
                             ROUND(SUM(rl.labour_minutes * frb.scaling_factor), 4) AS total_quantity,
                             'minutes' AS unit,
                             ROUND(COALESCE(labour_cost.rate_per_hour, 0) * (SUM(rl.labour_minutes * frb.scaling_factor) / 60), 4) AS total_cost
                         FROM
                             FullRecipeBreakdown AS frb
                                 INNER JOIN recipe AS r ON frb.recipe_id = r.recipe_id
                                 INNER JOIN recipe_labour AS rl ON frb.recipe_id = rl.recipe_id
                                 INNER JOIN labourer AS l ON rl.labourer_id = l.id
                                 INNER JOIN labour_category AS lc ON rl.labour_category_id = lc.id
                                 LEFT JOIN labour_cost ON l.id = labour_cost.labourer_id
                                 AND :date_point BETWEEN labour_cost.valid_from AND COALESCE(labour_cost.valid_to, '9999-12-31')
                                 CROSS JOIN -- Add top-level context to every row for convenience when working with chart tool tips etc. More convenient and efficient than another join
                                 (SELECT recipe_id, recipe_name, recipe_quantity, recipe_uom_id FROM recipe WHERE recipe_id = :top_recipe_id) AS top_level_recipe
                                 INNER JOIN unit_of_measure AS top_level_uom ON top_level_recipe.recipe_uom_id = top_level_uom.uom_id
                         GROUP BY
                             frb.recipe_id, r.recipe_name, frb.parent_recipe_id, l.id, l.name, lc.name, top_level_recipe.recipe_id,
                             top_level_recipe.recipe_name, top_level_recipe.recipe_quantity, top_level_uom.abbreviation, labour_cost.rate_per_hour

                         UNION ALL

                         -- Part 2: Ingredient Costs
                         SELECT
                             'Ingredient' AS cost_type,
                             frb.recipe_id,
                             r.recipe_name,
                             frb.parent_recipe_id,
                             i.ingredient_id AS item_id,
                             i.ingredient_name AS item_name,
                             'Raw Ingredient' AS item_category, -- Consistent category to avoid nulls in dataset. todo - replace this with commodity to allow for grouping and forecasting later
                             top_level_recipe.recipe_id AS top_level_recipe_id,
                             top_level_recipe.recipe_name AS top_level_recipe_name,
                             top_level_recipe.recipe_quantity AS top_level_batch_quantity,
                             top_level_uom.abbreviation AS top_level_uom,
                             ROUND(SUM((ri.quantity * uom_ingredient.conversion_factor) * frb.scaling_factor), 4) AS total_quantity,
                             uom_base.abbreviation AS unit,
                             ROUND(SUM((ri.quantity * uom_ingredient.conversion_factor) * frb.scaling_factor) * COALESCE(costs.cost_per_base_unit, 0), 4) AS total_cost

                         FROM
                             FullRecipeBreakdown AS frb
                                 INNER JOIN recipe_ingredient AS ri ON frb.recipe_id = ri.recipe_id
                                 INNER JOIN recipe AS r ON r.recipe_id = ri.recipe_id
                                 INNER JOIN ingredient AS i ON ri.ingredient_id = i.ingredient_id
                                 INNER JOIN unit_of_measure AS uom_ingredient ON ri.uom_id = uom_ingredient.uom_id
                                 INNER JOIN unit_of_measure AS uom_base ON uom_ingredient.base_uom_id = uom_base.uom_id
                                 LEFT JOIN v_ingredient_price_history AS costs ON costs.ingredient_id = ri.ingredient_id
                                 AND :date_point BETWEEN costs.from_date AND COALESCE(costs.valid_to, '9999-12-31')
                                 CROSS JOIN -- Add top-level context to every row
                                 (SELECT recipe_id, recipe_name, recipe_quantity, recipe_uom_id FROM recipe WHERE recipe_id = :top_recipe_id) AS top_level_recipe
                                 INNER JOIN unit_of_measure AS top_level_uom ON top_level_recipe.recipe_uom_id = top_level_uom.uom_id
                         GROUP BY
                             frb.recipe_id, r.recipe_name, frb.parent_recipe_id, i.ingredient_id, i.ingredient_name, uom_base.abbreviation,
                             top_level_recipe.recipe_id, top_level_recipe.recipe_name, top_level_recipe.recipe_quantity, top_level_uom.abbreviation, costs.cost_per_base_unit
                     )

-- FINAL SELECT: Calculate percentage of total and present all data
      SELECT
          *,  -- pass through all existing fields and add percentage of total
          -- Use a window function to get the grand total and calculate the percentage for each row to avoid having to add this in API logic
          -- NULLIF prevents division by zero if the total cost is 0.
          ROUND((total_cost / NULLIF(SUM(total_cost) OVER (), 0)) * 100, 4) AS percentage_of_total_cost
      FROM
          CombinedCosts

      ORDER BY
          recipe_id,
          cost_type,
          item_name;
""")