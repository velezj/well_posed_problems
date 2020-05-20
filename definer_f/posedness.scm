(define-module (well-posed posedness))

(use-modules (well-posed units)
	     (well-posed free-variables)
	     (srfi srfi-1))

;;;
;;; Determine if a representation is well posed
(define %representation-is-well-posed?
  (lambda (rep)
    (or (and (scheme-representation? rep)
	     (null? (compute-free-variables
		     (scheme-representation-object rep))))
	(and (compound-representation? rep)
	     (every (lambda (r) (%representation-is-well-posed? r))
		    (compound-representation-reps rep))))))


;;;
;;; A unit is well-posed IFF any one of it's representations is well-posed
(define is-unit-well-posed?
  (lambda (unit)
    (any %representation-is-well-posed
	 (unit-representations unit))))
