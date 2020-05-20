
(define-module (well-posed units))

(use-modules (srfi srfi-9)
	     (srfi srfi-9 gnu) )

;;;
;;; The basic block of a well founded problem is a
;;; unit
(define-immutable-record-type <unit>
  (make-unit representations parents children)
  unit?
  (representations unit-representations set-unit-representations)
  (parents unit-parents set-unit-parents)
  (children unit-children set-unit-children))
(export make-unit
	unit?
	unit-representations set-unit-representations
	unit-parents set-unit-parents
	unit-children set-unit-children)

;;;
;;; A "Representation" is a possible description of a unit.
;;;
;;; Possible representations include strings, programs, etc.

(define-immutable-record-type <string-representation>
  (make-string-representation string)
  string-representation?
  (string string-representation-string set-string-representation-string))
(export make-string-representation
	string-representation-string set-string-representation-string)

(define-immutable-record-type <scheme-representation>
  (make-scheme-representation object)
  scheme-representation?
  (object scheme-representation-object set-scheme-representation-object))
(export make-scheme-representation
	scheme-representation-object set-scheme-representation-object)


(define-immutable-record-type <compound-representation>
  (make-compound-representation reps)
  compound-representation?
  (reps compound-representation-reps set-compound-representation-reps))
(export make-compound-representation
	compound-representation-reps set-compound-representation-reps)

